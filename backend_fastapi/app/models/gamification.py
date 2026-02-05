"""Gamification models: Badges, Leaderboards, WeeklySummaries, AICache."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Badge(Base):
    """Badge definition model."""

    __tablename__ = "badges"

    id = Column(String(50), primary_key=True)  # e.g., 'first_session', 'streak_7'
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(100), nullable=False)  # emoji or icon name
    requirement = Column(Text, nullable=False)  # Human-readable requirement
    rarity = Column(String(20), nullable=False)  # common/rare/epic/legendary

    def __repr__(self):
        return f"<Badge {self.id}>"


class UserBadge(Base):
    """User's earned badges."""

    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    badge_id = Column(String(50), ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ensure user can only earn each badge once
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    # Relationships
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge")

    def __repr__(self):
        return f"<UserBadge {self.user_id} earned {self.badge_id}>"


class Leaderboard(Base):
    """Leaderboard model - cached/derived data."""

    __tablename__ = "leaderboards"

    id = Column(String(100), primary_key=True)  # e.g., 'hours-weekly-global'
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # hours/xp/productivity/streak
    period = Column(String(20), nullable=False)  # daily/weekly/monthly/all-time
    scope = Column(String(20), nullable=False)  # global/friends

    # Entries stored as JSONB array
    # Each entry: {user_id, display_name, photo_url, value, rank}
    entries = Column(JSONB, default=list, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Leaderboard {self.id}>"


class WeeklySummary(Base):
    """Weekly summary with AI-generated insights."""

    __tablename__ = "weekly_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Time range
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)

    # Stats
    total_hours = Column(Numeric(10, 2), nullable=False)
    total_sessions = Column(Integer, nullable=False)
    average_focus_score = Column(Numeric(3, 2), nullable=False)
    average_productivity_score = Column(Integer, nullable=False)
    xp_earned = Column(Integer, nullable=False)
    new_badges = Column(ARRAY(Text), default=list, nullable=False)
    streak_at_end = Column(Integer, nullable=False)

    # Topic breakdown: [{topic, minutes}]
    top_topics = Column(JSONB, default=list, nullable=False)

    # AI-generated content
    ai_summary = Column(Text, nullable=True)
    improvements = Column(ARRAY(Text), default=list, nullable=False)
    suggestions = Column(ARRAY(Text), default=list, nullable=False)

    # AI metadata for tracking
    ai_model = Column(String(50), nullable=True)  # gpt-4/gpt-3.5-turbo
    ai_prompt_hash = Column(String(64), nullable=True)  # for cache lookup
    regenerated_at = Column(DateTime, nullable=True)  # if manually regenerated

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WeeklySummary {self.user_id} {self.week_start}>"


class AICache(Base):
    """Cache for AI-generated content to avoid duplicate OpenAI calls."""

    __tablename__ = "ai_cache"

    prompt_hash = Column(String(64), primary_key=True)
    model = Column(String(50), nullable=False)
    response = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)

    def __repr__(self):
        return f"<AICache {self.prompt_hash[:8]}...>"
