"""Gamification endpoints: badges, XP, levels."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.gamification import Badge, UserBadge
from app.schemas.gamification import BadgeResponse, UserBadgeResponse
from app.services.gamification import check_and_award_badges

router = APIRouter()


@router.get("/badges", response_model=List[BadgeResponse])
async def list_badges(
    db: Session = Depends(get_db),
):
    """List all available badges."""
    badges = db.query(Badge).order_by(Badge.rarity.desc()).all()
    return badges


@router.get("/badges/user/{user_id}", response_model=List[UserBadgeResponse])
async def get_user_badges(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get badges earned by a user."""
    # Get user badges with badge details
    user_badges = (
        db.query(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .filter(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at.desc())
        .all()
    )

    return [
        UserBadgeResponse(
            id=ub.id,
            badge_id=badge.id,
            name=badge.name,
            description=badge.description,
            icon=badge.icon,
            rarity=badge.rarity,
            earned_at=ub.earned_at,
        )
        for ub, badge in user_badges
    ]


@router.get("/badges/{badge_id}", response_model=BadgeResponse)
async def get_badge(
    badge_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific badge by ID."""
    badge = db.query(Badge).filter(Badge.id == badge_id).first()

    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    return badge


@router.post("/gamification/check-badges")
async def trigger_badge_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check and award any earned badges for the current user."""
    new_badges = await check_and_award_badges(current_user.id, db)

    return {
        "new_badges": [
            {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "rarity": badge.rarity,
            }
            for badge in new_badges
        ],
        "count": len(new_badges),
    }


@router.get("/xp/progress")
async def get_xp_progress(
    current_user: User = Depends(get_current_user),
):
    """Get current XP progress and level information."""
    import math

    current_level = current_user.level
    current_xp = current_user.xp

    # XP needed for current level: level^2 * 100
    xp_for_current_level = current_level * current_level * 100
    xp_for_next_level = (current_level + 1) * (current_level + 1) * 100

    xp_in_current_level = current_xp - xp_for_current_level
    xp_needed_for_next = xp_for_next_level - xp_for_current_level
    progress_percent = (xp_in_current_level / xp_needed_for_next) * 100 if xp_needed_for_next > 0 else 100

    return {
        "current_xp": current_xp,
        "current_level": current_level,
        "xp_for_next_level": xp_for_next_level,
        "xp_in_current_level": xp_in_current_level,
        "xp_needed_for_next": xp_needed_for_next,
        "progress_percent": round(progress_percent, 1),
    }


@router.get("/streak")
async def get_streak_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current streak information."""
    from datetime import datetime, timedelta
    from app.models.session import Session as SessionModel

    # Check if user studied today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    studied_today = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == current_user.id,
            SessionModel.created_at >= today_start,
        )
        .first()
    ) is not None

    # Check if streak is still valid (studied yesterday if not today)
    yesterday_start = today_start - timedelta(days=1)
    studied_yesterday = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == current_user.id,
            SessionModel.created_at >= yesterday_start,
            SessionModel.created_at < today_start,
        )
        .first()
    ) is not None

    streak_active = studied_today or studied_yesterday

    return {
        "current_streak": current_user.streak if streak_active else 0,
        "longest_streak": current_user.longest_streak,
        "studied_today": studied_today,
        "streak_active": streak_active,
    }
