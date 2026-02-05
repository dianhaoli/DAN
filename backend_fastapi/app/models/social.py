"""Social models: Friends junction table, FriendRequests, Activities."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Friend(Base):
    """
    Friends junction table - replaces UUID[] array on users.
    
    This is a bidirectional relationship stored as two rows:
    - (user_A, user_B)
    - (user_B, user_A)
    
    Benefits:
    - Referential integrity (FKs ensure users exist)
    - Easy querying with JOINs
    - Can add metadata (created_at, blocked_at, etc.)
    - Scales better than arrays
    """

    __tablename__ = "friends"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    friend_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # Index for reverse lookups
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Friend {self.user_id} -> {self.friend_user_id}>"


class FriendRequest(Base):
    """Friend request model."""

    __tablename__ = "friend_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(20), default="pending", nullable=False)  # pending/accepted/rejected

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Ensure unique pending requests
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_friend_request"),
    )

    def __repr__(self):
        return f"<FriendRequest {self.from_user_id} -> {self.to_user_id} ({self.status})>"


class Activity(Base):
    """Activity feed item for social features."""

    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalized user info for fast feed loading
    user_name = Column(String(255), nullable=False)
    user_photo = Column(Text, nullable=True)

    # Activity type
    type = Column(String(50), nullable=False)  # session_complete/badge_earned/level_up/streak_milestone

    # Related entities (nullable based on type)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)

    # Activity-specific data
    topic = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    xp_earned = Column(Integer, nullable=True)
    badge_id = Column(String(50), nullable=True)
    badge_name = Column(String(100), nullable=True)
    new_level = Column(Integer, nullable=True)
    streak_days = Column(Integer, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Reactions stored as JSONB: {emoji: [user_ids]}
    reactions = Column(JSONB, default=dict, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.id} type={self.type}>"
