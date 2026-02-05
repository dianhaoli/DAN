"""Todo Pydantic schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TodoBase(BaseModel):
    """Base todo schema."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high)$")


class TodoCreate(TodoBase):
    """Schema for creating a todo."""

    pass


class TodoUpdate(BaseModel):
    """Schema for updating a todo."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")


class TodoResponse(BaseModel):
    """Todo response schema."""

    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    estimated_minutes: Optional[int]
    actual_minutes: Optional[int]
    due_date: Optional[datetime]
    scheduled_date: Optional[datetime]
    status: str
    completed_at: Optional[datetime]
    linked_session_id: Optional[UUID]
    category: Optional[str]
    priority: str
    xp_reward: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    """Paginated todo list response."""

    todos: List[TodoResponse]
    total: int
    skip: int
    limit: int
