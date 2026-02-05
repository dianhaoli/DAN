"""User Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    weekly_goal: Optional[int] = Field(None, ge=0)
    preferred_study_time: Optional[str] = None
    is_public: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""

    email: EmailStr
    firebase_uid: str


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    weekly_goal: Optional[int] = Field(None, ge=0)
    preferred_study_time: Optional[str] = None
    is_public: Optional[bool] = None


class UserResponse(BaseModel):
    """Full user response schema."""

    id: UUID
    email: str
    display_name: Optional[str]
    photo_url: Optional[str]
    username: Optional[str]
    xp: int
    level: int
    streak: int
    longest_streak: int
    total_study_time: int
    weekly_goal: Optional[int]
    preferred_study_time: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """Public user info - limited fields for privacy."""

    id: UUID
    display_name: Optional[str]
    username: Optional[str]
    photo_url: Optional[str]
    level: Optional[int]
    is_public: bool

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """User statistics response."""

    user_id: UUID
    total_sessions: int
    total_hours: float
    average_focus_score: float
    average_productivity_score: int
    topic_distribution: Dict[str, Any]
    study_heatmap: Dict[str, Any]
    weekly_trend: List[int]

    class Config:
        from_attributes = True
