"""Leaderboard service."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.social import Friend
from app.models.gamification import Leaderboard

logger = structlog.get_logger()


def get_user_rank(
    user_id: UUID,
    leaderboard_type: str,
    period: str,
    db: Session,
) -> Optional[Dict]:
    """Get user's rank and stats for a specific leaderboard."""
    leaderboard_id = f"{leaderboard_type}-{period}-global"
    leaderboard = db.query(Leaderboard).filter(Leaderboard.id == leaderboard_id).first()

    if not leaderboard:
        return None

    user_id_str = str(user_id)
    for entry in leaderboard.entries:
        if entry.get("user_id") == user_id_str:
            return {
                "rank": entry["rank"],
                "value": entry["value"],
                "total_entries": len(leaderboard.entries),
            }

    return None


def get_friends_leaderboard(
    user_id: UUID,
    leaderboard_type: str,
    period: str,
    db: Session,
    limit: int = 20,
) -> List[Dict]:
    """Get leaderboard filtered to friends only."""
    # Get friend IDs
    friend_ids = {
        str(f.friend_user_id)
        for f in db.query(Friend).filter(Friend.user_id == user_id).all()
    }
    friend_ids.add(str(user_id))  # Include self

    # Get global leaderboard
    leaderboard_id = f"{leaderboard_type}-{period}-global"
    leaderboard = db.query(Leaderboard).filter(Leaderboard.id == leaderboard_id).first()

    if not leaderboard:
        return []

    # Filter to friends
    friends_entries = [
        entry for entry in leaderboard.entries
        if entry.get("user_id") in friend_ids
    ]

    # Re-rank
    for i, entry in enumerate(friends_entries[:limit]):
        entry["rank"] = i + 1

    return friends_entries[:limit]


def calculate_hours_leaderboard(
    db: Session,
    period_start: Optional[datetime],
    limit: int = 100,
) -> List[Dict]:
    """Calculate hours leaderboard from sessions."""
    query = (
        db.query(
            User.id,
            User.display_name,
            User.photo_url,
            func.sum(SessionModel.duration).label("total_seconds"),
        )
        .join(SessionModel, SessionModel.user_id == User.id)
        .filter(User.is_public == True)
    )

    if period_start:
        query = query.filter(SessionModel.created_at >= period_start)

    results = (
        query.group_by(User.id, User.display_name, User.photo_url)
        .order_by(desc("total_seconds"))
        .limit(limit)
        .all()
    )

    return [
        {
            "user_id": str(r.id),
            "display_name": r.display_name or "Anonymous",
            "photo_url": r.photo_url,
            "value": round((r.total_seconds or 0) / 3600, 2),
            "rank": i + 1,
        }
        for i, r in enumerate(results)
    ]


def calculate_productivity_leaderboard(
    db: Session,
    period_start: Optional[datetime],
    min_sessions: int = 3,
    limit: int = 100,
) -> List[Dict]:
    """Calculate productivity leaderboard from sessions."""
    query = (
        db.query(
            User.id,
            User.display_name,
            User.photo_url,
            func.avg(SessionModel.productivity_score).label("avg_productivity"),
            func.count(SessionModel.id).label("session_count"),
        )
        .join(SessionModel, SessionModel.user_id == User.id)
        .filter(
            User.is_public == True,
            SessionModel.productivity_score.isnot(None),
        )
    )

    if period_start:
        query = query.filter(SessionModel.created_at >= period_start)

    results = (
        query.group_by(User.id, User.display_name, User.photo_url)
        .having(func.count(SessionModel.id) >= min_sessions)
        .order_by(desc("avg_productivity"))
        .limit(limit)
        .all()
    )

    return [
        {
            "user_id": str(r.id),
            "display_name": r.display_name or "Anonymous",
            "photo_url": r.photo_url,
            "value": round(float(r.avg_productivity), 1),
            "rank": i + 1,
        }
        for i, r in enumerate(results)
    ]


def get_period_start(period: str) -> Optional[datetime]:
    """Get the start datetime for a leaderboard period."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "daily":
        return today_start
    elif period == "weekly":
        return today_start - timedelta(days=today_start.weekday())
    elif period == "monthly":
        return today_start.replace(day=1)
    elif period == "all-time":
        return None
    else:
        return None
