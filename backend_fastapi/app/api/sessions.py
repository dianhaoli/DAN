"""Session endpoints with async ML pattern."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.session import Session as SessionModel
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
)
from app.workers.ml_tasks import process_session_ml

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new session with async ML processing."""
    # Create session with pending status
    session = SessionModel(
        user_id=current_user.id,
        start_time=session_data.start_time,
        end_time=session_data.end_time,
        duration=session_data.duration,
        topic=session_data.topic,
        category=session_data.category,
        domains=session_data.domains or [],
        title=session_data.title,
        tab_switches=session_data.tab_switches or 0,
        active_time=session_data.active_time or session_data.duration,
        idle_time=session_data.idle_time or 0,
        clicks=session_data.clicks,
        keystrokes=session_data.keystrokes,
        source=session_data.source or "extension",
        platform=session_data.platform,
        processing_status="pending",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    # Queue ML processing task
    process_session_ml.delay(str(session.id))

    return session


@router.get("", response_model=SessionListResponse)
@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
):
    """List user's sessions with pagination and filters."""
    query = db.query(SessionModel).filter(SessionModel.user_id == current_user.id)

    if start_date:
        query = query.filter(SessionModel.start_time >= start_date)
    if end_date:
        query = query.filter(SessionModel.end_time <= end_date)
    if topic:
        query = query.filter(SessionModel.topic.ilike(f"%{topic}%"))
    if status:
        query = query.filter(SessionModel.processing_status == status)

    total = query.count()
    sessions = query.order_by(SessionModel.created_at.desc()).offset(skip).limit(limit).all()

    return SessionListResponse(
        sessions=sessions,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single session by ID."""
    session = (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a session."""
    session = (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a session."""
    session = (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()


@router.get("/stats/summary")
async def get_session_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=365),
):
    """Get session statistics for the user."""
    from datetime import timedelta
    from sqlalchemy import func

    start_date = datetime.utcnow() - timedelta(days=days)

    stats = (
        db.query(
            func.count(SessionModel.id).label("total_sessions"),
            func.sum(SessionModel.duration).label("total_duration"),
            func.avg(SessionModel.focus_score).label("avg_focus_score"),
            func.avg(SessionModel.productivity_score).label("avg_productivity_score"),
        )
        .filter(
            SessionModel.user_id == current_user.id,
            SessionModel.created_at >= start_date,
        )
        .first()
    )

    return {
        "total_sessions": stats.total_sessions or 0,
        "total_duration": stats.total_duration or 0,
        "total_hours": round((stats.total_duration or 0) / 3600, 2),
        "avg_focus_score": round(float(stats.avg_focus_score or 0), 2),
        "avg_productivity_score": round(float(stats.avg_productivity_score or 0), 0),
        "period_days": days,
    }
