"""Session SQLAlchemy model with ML tracking fields."""

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
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    """Study session model with async ML processing support."""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time tracking
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=False)  # seconds

    # Content
    topic = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    domains = Column(ARRAY(Text), default=list, nullable=False)
    title = Column(String(500), nullable=True)

    # Metrics (from extension)
    tab_switches = Column(Integer, default=0, nullable=False)
    active_time = Column(Integer, default=0, nullable=False)  # seconds
    idle_time = Column(Integer, default=0, nullable=False)  # seconds
    clicks = Column(Integer, nullable=True)
    keystrokes = Column(Integer, nullable=True)

    # ML predictions (populated async)
    focus_score = Column(Numeric(3, 2), nullable=True)  # 0-1
    productivity_score = Column(Integer, nullable=True)  # 0-100
    activity_label = Column(String(50), nullable=True)  # study/distraction/research

    # ML tracking - for debugging and versioning
    processing_status = Column(String(20), default="pending", nullable=False)  # pending/processing/completed/failed
    ml_model_version = Column(String(100), nullable=True)  # e.g., 'distilbert-v1.0+xgb-v1.2'
    ml_features = Column(JSONB, nullable=True)  # raw features used for prediction
    ml_processed_at = Column(DateTime, nullable=True)

    # Source info
    source = Column(String(50), default="extension", nullable=False)  # extension/manual
    platform = Column(String(50), nullable=True)

    # AI-generated content
    ai_summary = Column(Text, nullable=True)
    topics = Column(ARRAY(Text), nullable=True)

    # Gamification
    xp_earned = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    activities = relationship("Activity", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session {self.id} topic={self.topic}>"
