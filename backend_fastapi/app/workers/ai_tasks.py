"""Celery tasks for async AI (OpenAI) operations."""

from datetime import datetime

import structlog

from app.workers import celery_app
from app.database import SessionLocal
from app.models.session import Session
from app.models.gamification import WeeklySummary
from app.ai.client import (
    generate_session_summary_text,
    generate_task_breakdown_text,
    generate_weekly_summary_text,
)

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_session_summary(self, session_id: str, user_id: str) -> dict:
    """
    Generate AI summary for a session.
    
    Args:
        session_id: UUID of the session
        user_id: UUID of the user (for verification)
        
    Returns:
        Dictionary with summary and metadata
    """
    logger.info("Generating session summary", session_id=session_id)

    db = SessionLocal()
    try:
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id,
        ).first()

        if not session:
            return {"error": "Session not found"}

        # Generate summary using OpenAI
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            summary = loop.run_until_complete(
                generate_session_summary_text(
                    topic=session.topic,
                    duration_minutes=session.duration // 60,
                    domains=session.domains or [],
                    productivity_score=session.productivity_score,
                    activity_label=session.activity_label,
                )
            )
        finally:
            loop.close()

        # Update session with summary
        session.ai_summary = summary
        db.commit()

        logger.info("Session summary generated", session_id=session_id)

        return {
            "status": "completed",
            "session_id": session_id,
            "summary": summary,
        }

    except Exception as e:
        logger.error("Session summary generation failed", session_id=session_id, error=str(e))
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_task_breakdown(
    self,
    task_title: str,
    task_description: str,
    estimated_minutes: int,
    user_id: str,
) -> dict:
    """
    Break down a task into subtasks using AI.
    
    Args:
        task_title: Title of the task
        task_description: Optional description
        estimated_minutes: Optional time estimate
        user_id: UUID of the requesting user
        
    Returns:
        Dictionary with subtasks and suggestions
    """
    logger.info("Generating task breakdown", task_title=task_title, user_id=user_id)

    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                generate_task_breakdown_text(
                    task_title=task_title,
                    task_description=task_description,
                    estimated_minutes=estimated_minutes,
                )
            )
        finally:
            loop.close()

        # Parse the response into structured subtasks
        subtasks = parse_task_breakdown(result["raw_response"])

        logger.info("Task breakdown generated", task_title=task_title, subtask_count=len(subtasks))

        return {
            "status": "completed",
            "original_task": task_title,
            "subtasks": subtasks,
            "raw_response": result["raw_response"],
            "model": result["model"],
            "tokens_used": result["tokens_used"],
        }

    except Exception as e:
        logger.error("Task breakdown failed", task_title=task_title, error=str(e))
        raise self.retry(exc=e)


@celery_app.task(bind=True)
def generate_weekly_summary_task(self, user_id: str, week_start: str, week_end: str) -> dict:
    """
    Generate weekly summary for a user.
    
    This is typically called by a scheduled job.
    """
    from datetime import datetime
    from sqlalchemy import func

    logger.info("Generating weekly summary", user_id=user_id)

    db = SessionLocal()
    try:
        from app.models.user import User
        from app.models.gamification import UserBadge

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}

        week_start_dt = datetime.fromisoformat(week_start)
        week_end_dt = datetime.fromisoformat(week_end)

        # Get session stats for the week
        sessions = (
            db.query(Session)
            .filter(
                Session.user_id == user_id,
                Session.created_at >= week_start_dt,
                Session.created_at <= week_end_dt,
            )
            .all()
        )

        if not sessions:
            return {"status": "skipped", "reason": "No sessions this week"}

        # Calculate stats
        total_hours = sum(s.duration for s in sessions) / 3600
        total_sessions = len(sessions)
        avg_productivity = sum(s.productivity_score or 0 for s in sessions) / len(sessions)
        avg_focus = sum(float(s.focus_score or 0) for s in sessions) / len(sessions)

        # Get top topics
        topic_minutes = {}
        for s in sessions:
            topic = s.topic
            minutes = s.duration // 60
            topic_minutes[topic] = topic_minutes.get(topic, 0) + minutes

        top_topics = [
            {"topic": t, "minutes": m}
            for t, m in sorted(topic_minutes.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Get XP earned this week
        xp_earned = sum(s.xp_earned for s in sessions)

        # Get new badges this week
        new_badges = (
            db.query(UserBadge)
            .filter(
                UserBadge.user_id == user_id,
                UserBadge.earned_at >= week_start_dt,
                UserBadge.earned_at <= week_end_dt,
            )
            .all()
        )
        new_badge_ids = [b.badge_id for b in new_badges]

        # Generate AI summary
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            ai_result = loop.run_until_complete(
                generate_weekly_summary_text(
                    total_hours=total_hours,
                    total_sessions=total_sessions,
                    avg_productivity=int(avg_productivity),
                    top_topics=top_topics,
                    streak=user.streak,
                    xp_earned=xp_earned,
                )
            )
        finally:
            loop.close()

        # Parse improvements and suggestions from AI response
        improvements, suggestions = parse_weekly_summary(ai_result["summary"])

        # Create weekly summary record
        summary = WeeklySummary(
            user_id=user.id,
            week_start=week_start_dt,
            week_end=week_end_dt,
            total_hours=total_hours,
            total_sessions=total_sessions,
            average_focus_score=avg_focus,
            average_productivity_score=int(avg_productivity),
            xp_earned=xp_earned,
            new_badges=new_badge_ids,
            streak_at_end=user.streak,
            top_topics=top_topics,
            ai_summary=ai_result["summary"],
            improvements=improvements,
            suggestions=suggestions,
            ai_model=ai_result["model"],
            ai_prompt_hash=ai_result["prompt_hash"],
        )

        db.add(summary)
        db.commit()

        logger.info("Weekly summary generated", user_id=user_id)

        return {
            "status": "completed",
            "user_id": user_id,
            "total_hours": total_hours,
            "total_sessions": total_sessions,
        }

    except Exception as e:
        logger.error("Weekly summary generation failed", user_id=user_id, error=str(e))
        raise

    finally:
        db.close()


def parse_task_breakdown(response: str) -> list:
    """Parse AI response into structured subtasks."""
    subtasks = []
    lines = response.strip().split("\n")

    current_task = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for numbered items
        if line[0].isdigit() and "." in line:
            if current_task:
                subtasks.append(current_task)

            # Extract title
            title = line.split(".", 1)[1].strip() if "." in line else line
            current_task = {
                "title": title,
                "description": None,
                "estimated_minutes": 15,  # Default
                "priority": "medium",
            }
        elif current_task:
            # Look for time estimates
            if "minute" in line.lower() or "min" in line.lower():
                import re
                match = re.search(r"(\d+)\s*(minute|min)", line.lower())
                if match:
                    current_task["estimated_minutes"] = int(match.group(1))

            # Look for priority
            if "high" in line.lower():
                current_task["priority"] = "high"
            elif "low" in line.lower():
                current_task["priority"] = "low"

    if current_task:
        subtasks.append(current_task)

    return subtasks


def parse_weekly_summary(summary: str) -> tuple:
    """Parse weekly summary for improvements and suggestions."""
    improvements = []
    suggestions = []

    lines = summary.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if "improvement" in line.lower() or "area" in line.lower():
            current_section = "improvements"
        elif "suggestion" in line.lower() or "recommendation" in line.lower():
            current_section = "suggestions"
        elif line.startswith("-") or line.startswith("•"):
            content = line[1:].strip()
            if current_section == "improvements":
                improvements.append(content)
            elif current_section == "suggestions":
                suggestions.append(content)

    return improvements[:3], suggestions[:3]
