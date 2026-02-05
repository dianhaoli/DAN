"""Gamification Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class BadgeResponse(BaseModel):
    """Badge response schema."""

    id: str
    name: str
    description: str
    icon: str
    requirement: str
    rarity: str

    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    """User's earned badge response."""

    id: UUID
    badge_id: str
    name: str
    description: str
    icon: str
    rarity: str
    earned_at: datetime


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""

    user_id: str
    display_name: str
    photo_url: Optional[str]
    value: float
    rank: int


class LeaderboardResponse(BaseModel):
    """Leaderboard response schema."""

    id: str
    name: str
    type: str
    period: str
    scope: str
    entries: List[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True


class WeeklySummaryResponse(BaseModel):
    """Weekly summary response schema."""

    id: UUID
    user_id: UUID
    week_start: datetime
    week_end: datetime
    total_hours: float
    total_sessions: int
    average_focus_score: float
    average_productivity_score: int
    xp_earned: int
    new_badges: List[str]
    streak_at_end: int
    top_topics: List[Dict[str, Any]]
    ai_summary: Optional[str]
    improvements: List[str]
    suggestions: List[str]
    ai_model: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
