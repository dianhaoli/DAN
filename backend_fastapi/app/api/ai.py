"""AI endpoints with quotas for OpenAI integration."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import check_ai_quota
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.gamification import WeeklySummary
from app.schemas.ai import (
    SummarizeSessionRequest,
    SummarizeSessionResponse,
    BreakdownTaskRequest,
    BreakdownTaskResponse,
    InsightsRequest,
    InsightsResponse,
)
from app.schemas.gamification import WeeklySummaryResponse
from app.workers.ai_tasks import generate_session_summary, generate_task_breakdown

router = APIRouter()


@router.post("/summarize-session", response_model=SummarizeSessionResponse)
async def summarize_session(
    request: SummarizeSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _quota: None = Depends(check_ai_quota),
):
    """Generate AI summary for a session."""
    # Verify session ownership
    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == request.session_id,
            SessionModel.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Queue async task and return task ID
    task = generate_session_summary.delay(
        str(session.id),
        str(current_user.id),
    )

    return SummarizeSessionResponse(
        task_id=task.id,
        status="processing",
        message="Summary generation queued",
    )


@router.post("/breakdown-task", response_model=BreakdownTaskResponse)
async def breakdown_task(
    request: BreakdownTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _quota: None = Depends(check_ai_quota),
):
    """Break down a complex task into subtasks using AI."""
    # Queue async task
    task = generate_task_breakdown.delay(
        request.task_title,
        request.task_description,
        request.estimated_minutes,
        str(current_user.id),
    )

    return BreakdownTaskResponse(
        task_id=task.id,
        status="processing",
        message="Task breakdown queued",
    )


@router.get("/breakdown-task/{task_id}")
async def get_breakdown_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the result of a task breakdown."""
    from celery.result import AsyncResult
    from app.workers import celery_app

    result = AsyncResult(task_id, app=celery_app)

    if result.ready():
        if result.successful():
            return {
                "status": "completed",
                "result": result.get(),
            }
        else:
            return {
                "status": "failed",
                "error": str(result.result),
            }
    else:
        return {
            "status": "processing",
        }


@router.get("/weekly-summary/{user_id}", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the latest weekly summary for a user."""
    # Privacy check
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Can only view your own weekly summary",
        )

    summary = (
        db.query(WeeklySummary)
        .filter(WeeklySummary.user_id == user_id)
        .order_by(WeeklySummary.week_end.desc())
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="No weekly summary found")

    return summary


@router.post("/insights", response_model=InsightsResponse)
async def generate_insights(
    request: InsightsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _quota: None = Depends(check_ai_quota),
):
    """Generate productivity insights based on user's session history."""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # Get session stats for the requested period
    days = request.days or 30
    start_date = datetime.utcnow() - timedelta(days=days)

    sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == current_user.id,
            SessionModel.created_at >= start_date,
            SessionModel.processing_status == "completed",
        )
        .all()
    )

    if not sessions:
        return InsightsResponse(
            insights=[],
            recommendations=[],
            message="Not enough data to generate insights",
        )

    # Calculate basic stats
    total_hours = sum(s.duration for s in sessions) / 3600
    avg_productivity = sum(s.productivity_score or 0 for s in sessions) / len(sessions)
    avg_focus = sum(s.focus_score or 0 for s in sessions) / len(sessions)

    # Find best times
    hour_counts = {}
    for s in sessions:
        hour = s.start_time.hour
        if hour not in hour_counts:
            hour_counts[hour] = {"count": 0, "productivity": 0}
        hour_counts[hour]["count"] += 1
        hour_counts[hour]["productivity"] += s.productivity_score or 0

    best_hours = sorted(
        hour_counts.items(),
        key=lambda x: x[1]["productivity"] / x[1]["count"] if x[1]["count"] > 0 else 0,
        reverse=True,
    )[:3]

    insights = [
        f"You've studied {total_hours:.1f} hours over the past {days} days",
        f"Your average productivity score is {avg_productivity:.0f}/100",
        f"Your average focus score is {avg_focus:.2f}",
    ]

    recommendations = []
    if best_hours:
        best_hour = best_hours[0][0]
        recommendations.append(
            f"Your most productive time is around {best_hour}:00 - try to schedule important tasks then"
        )

    if avg_productivity < 50:
        recommendations.append(
            "Consider taking more breaks and minimizing distractions during study sessions"
        )

    return InsightsResponse(
        insights=insights,
        recommendations=recommendations,
        stats={
            "total_hours": round(total_hours, 2),
            "total_sessions": len(sessions),
            "avg_productivity": round(avg_productivity, 0),
            "avg_focus": round(avg_focus, 2),
            "best_hours": [h[0] for h in best_hours],
        },
    )
