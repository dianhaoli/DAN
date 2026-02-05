"""AI endpoint Pydantic schemas."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SummarizeSessionRequest(BaseModel):
    """Request to summarize a session."""

    session_id: UUID


class SummarizeSessionResponse(BaseModel):
    """Response for session summarization (async)."""

    task_id: str
    status: str
    message: str


class BreakdownTaskRequest(BaseModel):
    """Request to break down a task."""

    task_title: str = Field(..., min_length=1, max_length=500)
    task_description: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)


class BreakdownTaskResponse(BaseModel):
    """Response for task breakdown (async)."""

    task_id: str
    status: str
    message: str


class SubtaskResult(BaseModel):
    """A subtask from AI breakdown."""

    title: str
    description: Optional[str]
    estimated_minutes: int
    priority: str


class TaskBreakdownResult(BaseModel):
    """Full result of task breakdown."""

    original_task: str
    subtasks: List[SubtaskResult]
    total_estimated_minutes: int
    suggestions: List[str]


class InsightsRequest(BaseModel):
    """Request for productivity insights."""

    days: Optional[int] = Field(30, ge=1, le=365)


class InsightsResponse(BaseModel):
    """Productivity insights response."""

    insights: List[str]
    recommendations: List[str]
    stats: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
