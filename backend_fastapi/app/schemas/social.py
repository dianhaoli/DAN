"""Social Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class FriendRequestCreate(BaseModel):
    """Schema for creating a friend request."""

    to_user_id: UUID


class FriendRequestResponse(BaseModel):
    """Friend request response schema."""

    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FriendResponse(BaseModel):
    """Friend response schema with user info."""

    user_id: UUID
    display_name: Optional[str]
    username: Optional[str]
    photo_url: Optional[str]
    level: int
    friends_since: datetime


class ActivityResponse(BaseModel):
    """Activity feed item response."""

    id: UUID
    user_id: UUID
    user_name: str
    user_photo: Optional[str]
    type: str
    session_id: Optional[UUID]
    topic: Optional[str]
    duration: Optional[int]
    xp_earned: Optional[int]
    badge_id: Optional[str]
    badge_name: Optional[str]
    new_level: Optional[int]
    streak_days: Optional[int]
    timestamp: datetime
    reactions: Dict[str, List[str]]

    class Config:
        from_attributes = True


class ReactionCreate(BaseModel):
    """Schema for adding a reaction."""

    emoji: str
