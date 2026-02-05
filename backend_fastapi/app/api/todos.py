"""Todo CRUD endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new todo."""
    try:
        # Calculate XP reward based on estimated time and priority
        xp_reward = calculate_xp_reward(
            todo_data.estimated_minutes,
            todo_data.priority,
        )

        todo = Todo(
            user_id=current_user.id,
            title=todo_data.title,
            description=todo_data.description,
            estimated_minutes=todo_data.estimated_minutes,
            due_date=todo_data.due_date,
            scheduled_date=todo_data.scheduled_date,
            category=todo_data.category,
            priority=todo_data.priority or "medium",
            xp_reward=xp_reward,
        )

        db.add(todo)
        db.commit()
        db.refresh(todo)

        logger.info(
            "Todo created successfully",
            todo_id=str(todo.id),
            user_id=str(current_user.id),
            title=todo.title,
        )

        return todo
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "Database error creating todo",
            error=str(e),
            user_id=str(current_user.id),
            title=todo_data.title,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create todo: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "Unexpected error creating todo",
            error=str(e),
            user_id=str(current_user.id),
            title=todo_data.title,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create todo: {str(e)}",
        )


@router.get("/", response_model=TodoListResponse)
async def list_todos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    category: Optional[str] = None,
):
    """List user's todos with pagination and filters."""
    query = db.query(Todo).filter(Todo.user_id == current_user.id)

    if status_filter:
        query = query.filter(Todo.status == status_filter)
    if priority:
        query = query.filter(Todo.priority == priority)
    if category:
        query = query.filter(Todo.category == category)

    total = query.count()
    todos = (
        query.order_by(Todo.due_date.asc().nullslast(), Todo.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return TodoListResponse(
        todos=todos,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single todo by ID."""
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == current_user.id)
        .first()
    )

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: UUID,
    todo_update: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a todo."""
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == current_user.id)
        .first()
    )

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    todo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(todo)

    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a todo."""
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == current_user.id)
        .first()
    )

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo)
    db.commit()


@router.post("/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(
    todo_id: UUID,
    actual_minutes: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a todo as completed and award XP."""
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == current_user.id)
        .first()
    )

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if todo.status == "completed":
        raise HTTPException(status_code=400, detail="Todo already completed")

    # Update todo
    todo.status = "completed"
    todo.completed_at = datetime.utcnow()
    todo.actual_minutes = actual_minutes

    # Award XP to user
    current_user.xp += todo.xp_reward

    # Check for level up
    new_level = calculate_level(current_user.xp)
    leveled_up = new_level > current_user.level
    if leveled_up:
        current_user.level = new_level

    db.commit()
    db.refresh(todo)

    return todo


def calculate_xp_reward(estimated_minutes: Optional[int], priority: Optional[str]) -> int:
    """Calculate XP reward for a todo based on time and priority."""
    base_xp = 10

    if estimated_minutes:
        # 1 XP per minute, capped at 100
        base_xp += min(estimated_minutes, 100)

    # Priority multiplier
    multipliers = {"low": 1, "medium": 1.5, "high": 2}
    multiplier = multipliers.get(priority or "medium", 1.5)

    return int(base_xp * multiplier)


def calculate_level(xp: int) -> int:
    """Calculate level from XP using exponential curve."""
    # Level formula: XP needed = level^2 * 100
    import math
    return int(math.sqrt(xp / 100))
