"""Leaderboard endpoints with admin protection."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.models.social import Friend
from app.models.gamification import Leaderboard
from app.schemas.gamification import LeaderboardResponse
from app.workers.stats_tasks import update_leaderboards

router = APIRouter()


@router.get("/", response_model=List[LeaderboardResponse])
async def list_leaderboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period: Optional[str] = Query(None, regex="^(daily|weekly|monthly|all-time)$"),
    type: Optional[str] = Query(None, regex="^(hours|xp|productivity|streak)$"),
):
    """List all leaderboards with optional filters."""
    query = db.query(Leaderboard)

    if period:
        query = query.filter(Leaderboard.period == period)
    if type:
        query = query.filter(Leaderboard.type == type)

    leaderboards = query.all()
    return leaderboards


@router.get("/{leaderboard_id}", response_model=LeaderboardResponse)
async def get_leaderboard(
    leaderboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific leaderboard."""
    leaderboard = db.query(Leaderboard).filter(Leaderboard.id == leaderboard_id).first()

    if not leaderboard:
        raise HTTPException(status_code=404, detail="Leaderboard not found")

    return leaderboard


@router.get("/friends/{type}/{period}")
async def get_friends_leaderboard(
    type: str,
    period: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get leaderboard filtered to friends only."""
    # Validate type and period
    valid_types = ["hours", "xp", "productivity", "streak"]
    valid_periods = ["daily", "weekly", "monthly", "all-time"]

    if type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Must be one of: {valid_periods}")

    # Get leaderboard
    leaderboard_id = f"{type}-{period}-global"
    leaderboard = db.query(Leaderboard).filter(Leaderboard.id == leaderboard_id).first()

    if not leaderboard:
        return {"entries": [], "type": type, "period": period, "scope": "friends"}

    # Get friend IDs
    friend_ids = {
        str(f.friend_user_id)
        for f in db.query(Friend).filter(Friend.user_id == current_user.id).all()
    }
    friend_ids.add(str(current_user.id))  # Include self

    # Filter entries to friends only
    entries = leaderboard.entries or []
    friends_entries = [
        entry for entry in entries
        if entry.get("user_id") in friend_ids
    ]

    # Re-rank
    for i, entry in enumerate(friends_entries):
        entry["rank"] = i + 1

    return {
        "entries": friends_entries,
        "type": type,
        "period": period,
        "scope": "friends",
    }


@router.post("/update", status_code=status.HTTP_202_ACCEPTED)
async def trigger_leaderboard_update(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Trigger leaderboard recalculation.
    
    ADMIN ONLY - This is a protected endpoint that triggers expensive
    database operations. Only users with admin role can call this.
    """
    # Queue the update task
    update_leaderboards.delay()

    return {
        "status": "accepted",
        "message": "Leaderboard update queued",
    }
