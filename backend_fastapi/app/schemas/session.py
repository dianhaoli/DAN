"""Session Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SessionBase(BaseModel):
    """Base session schema."""

    topic: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    domains: Optional[List[str]] = []
    title: Optional[str] = Field(None, max_length=500)


class SessionCreate(SessionBase):
    """Schema for creating a session."""

    start_time: datetime
    end_time: Optional[datetime] = None
    duration: int = Field(..., ge=0)  # seconds
    tab_switches: Optional[int] = Field(0, ge=0)
    active_time: Optional[int] = Field(None, ge=0)
    idle_time: Optional[int] = Field(0, ge=0)
    clicks: Optional[int] = Field(None, ge=0)
    keystrokes: Optional[int] = Field(None, ge=0)
    source: Optional[str] = "extension"
    platform: Optional[str] = None


class SessionUpdate(BaseModel):
    """Schema for updating a session."""

    topic: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=500)
    end_time: Optional[datetime] = None


class SessionResponse(BaseModel):
    """Session response schema."""

    id: UUID
    user_id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    duration: int
    topic: str
    category: Optional[str]
    domains: List[str]
    title: Optional[str]

    # Metrics
    tab_switches: int
    active_time: int
    idle_time: int
    clicks: Optional[int]
    keystrokes: Optional[int]

    # ML predictions
    focus_score: Optional[float]
    productivity_score: Optional[int]
    activity_label: Optional[str]

    # ML tracking
    processing_status: str
    ml_model_version: Optional[str]
    ml_features: Optional[Dict[str, Any]]
    ml_processed_at: Optional[datetime]

    # Source
    source: str
    platform: Optional[str]

    # AI content
    ai_summary: Optional[str]
    topics: Optional[List[str]]

    # Gamification
    xp_earned: int

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Paginated session list response."""

    sessions: List[SessionResponse]
    total: int
    skip: int
    limit: int
