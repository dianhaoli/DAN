"""Todo SQLAlchemy model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Todo(Base):
    """Todo/task model."""

    __tablename__ = "todos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Time estimates
    estimated_minutes = Column(Integer, nullable=True)
    actual_minutes = Column(Integer, nullable=True)

    # Scheduling
    due_date = Column(DateTime, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)

    # Status
    status = Column(String(20), default="pending", nullable=False)  # pending/in_progress/completed/cancelled
    completed_at = Column(DateTime, nullable=True)

    # Linked session (if completed during a session)
    linked_session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)

    # Organization
    category = Column(String(100), nullable=True)
    priority = Column(String(20), default="medium", nullable=False)  # low/medium/high

    # Gamification
    xp_reward = Column(Integer, default=10, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="todos")

    def __repr__(self):
        return f"<Todo {self.id} title={self.title[:30]}...>"
