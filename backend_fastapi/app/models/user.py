"""User-related SQLAlchemy models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    photo_url = Column(Text, nullable=True)
    username = Column(String(50), unique=True, nullable=True, index=True)

    # Gamification
    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=0, nullable=False)
    streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    total_study_time = Column(Integer, default=0, nullable=False)  # minutes

    # Settings
    weekly_goal = Column(Integer, nullable=True)  # minutes
    preferred_study_time = Column(String(50), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="user", cascade="all, delete-orphan")
    stats = relationship("UserStats", back_populates="user", uselist=False, cascade="all, delete-orphan")
    quota = relationship("UserQuota", back_populates="user", uselist=False, cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class UserStats(Base):
    """User statistics - derived/cached data, updated by background jobs only."""

    __tablename__ = "user_stats"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    total_sessions = Column(Integer, default=0, nullable=False)
    total_hours = Column(Numeric(10, 2), default=0, nullable=False)
    average_focus_score = Column(Numeric(3, 2), default=0, nullable=False)
    average_productivity_score = Column(Integer, default=0, nullable=False)

    # JSONB for flexible data
    topic_distribution = Column(JSONB, default=dict, nullable=False)  # {topic: minutes}
    study_heatmap = Column(JSONB, default=dict, nullable=False)  # {date: minutes}
    weekly_trend = Column(JSONB, default=list, nullable=False)  # last 12 weeks

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="stats")

    def __repr__(self):
        return f"<UserStats user_id={self.user_id}>"


class UserQuota(Base):
    """User API quotas for rate limiting."""

    __tablename__ = "user_quotas"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    ai_requests_today = Column(Integer, default=0, nullable=False)
    ai_requests_reset_at = Column(DateTime, nullable=True)
    last_request_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="quota")

    def __repr__(self):
        return f"<UserQuota user_id={self.user_id}>"
