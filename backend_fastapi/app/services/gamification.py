"""Gamification service for badge checking and awarding."""

from datetime import datetime, timedelta
from typing import List
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.gamification import Badge, UserBadge
from app.models.social import Activity

logger = structlog.get_logger()

# Badge definitions - synced with shared package (@dan/shared)
# Uses both hyphen and underscore IDs for compatibility
BADGE_DEFINITIONS = [
    # Session count badges
    {
        "id": "first-session",  # Matches shared package
        "name": "First Steps",
        "description": "Complete your first study session",
        "icon": "🎯",
        "requirement": "1 session",
        "rarity": "common",
        "check": lambda stats: stats["total_sessions"] >= 1,
    },
    {
        "id": "session_10",
        "name": "Getting Started",
        "description": "Complete 10 study sessions",
        "icon": "📚",
        "requirement": "10 sessions",
        "rarity": "common",
        "check": lambda stats: stats["total_sessions"] >= 10,
    },
    {
        "id": "session_50",
        "name": "Dedicated Learner",
        "description": "Complete 50 study sessions",
        "icon": "🎓",
        "requirement": "50 sessions",
        "rarity": "rare",
        "check": lambda stats: stats["total_sessions"] >= 50,
    },
    {
        "id": "session_100",
        "name": "Study Master",
        "description": "Complete 100 study sessions",
        "icon": "🏆",
        "requirement": "100 sessions",
        "rarity": "epic",
        "check": lambda stats: stats["total_sessions"] >= 100,
    },
    # Streak badges (synced with shared package)
    {
        "id": "streak-5",  # Matches shared package
        "name": "Consistent",
        "description": "Maintain a 5-day study streak",
        "icon": "🔥",
        "requirement": "5 day streak",
        "rarity": "common",
        "check": lambda stats: stats["streak"] >= 5,
    },
    {
        "id": "streak_7",
        "name": "Week Warrior",
        "description": "Maintain a 7-day study streak",
        "icon": "⚡",
        "requirement": "7 day streak",
        "rarity": "rare",
        "check": lambda stats: stats["streak"] >= 7,
    },
    {
        "id": "streak-30",  # Matches shared package
        "name": "Dedicated",
        "description": "Maintain a 30-day study streak",
        "icon": "🔥🔥",
        "requirement": "30 day streak",
        "rarity": "rare",
        "check": lambda stats: stats["streak"] >= 30,
    },
    {
        "id": "streak-100",  # Matches shared package
        "name": "Unstoppable",
        "description": "Maintain a 100-day study streak",
        "icon": "🔥🔥🔥",
        "requirement": "100 day streak",
        "rarity": "legendary",
        "check": lambda stats: stats["streak"] >= 100,
    },
    # Hours badges (synced with shared package)
    {
        "id": "hours-10",  # Matches shared package
        "name": "Getting Started",
        "description": "Study for 10 total hours",
        "icon": "⏰",
        "requirement": "10 hours",
        "rarity": "common",
        "check": lambda stats: stats["total_hours"] >= 10,
    },
    {
        "id": "hours_50",
        "name": "Dedicated Timer",
        "description": "Study for 50 total hours",
        "icon": "⏱️",
        "requirement": "50 hours",
        "rarity": "rare",
        "check": lambda stats: stats["total_hours"] >= 50,
    },
    {
        "id": "hours-100",  # Matches shared package
        "name": "Committed Learner",
        "description": "Study for 100 total hours",
        "icon": "📚",
        "requirement": "100 hours",
        "rarity": "rare",
        "check": lambda stats: stats["total_hours"] >= 100,
    },
    {
        "id": "hours-1000",  # Matches shared package
        "name": "Master Scholar",
        "description": "Study for 1000 total hours",
        "icon": "🎓",
        "requirement": "1000 hours",
        "rarity": "legendary",
        "check": lambda stats: stats["total_hours"] >= 1000,
    },
    # Focus/productivity badges
    {
        "id": "focus-hero",  # Matches shared package
        "name": "Focus Hero",
        "description": "Achieve 95%+ focus score in a session",
        "icon": "🎯",
        "requirement": "95% focus",
        "rarity": "rare",
        "check": lambda stats: stats.get("highest_focus_score", 0) >= 0.95,
    },
    {
        "id": "productivity_high",
        "name": "Peak Performance",
        "description": "Achieve 90+ productivity in a session",
        "icon": "🚀",
        "requirement": "90+ productivity",
        "rarity": "rare",
        "check": lambda stats: stats["max_productivity"] >= 90,
    },
    # Level badges
    {
        "id": "level_5",
        "name": "Rising Star",
        "description": "Reach level 5",
        "icon": "⭐",
        "requirement": "Level 5",
        "rarity": "common",
        "check": lambda stats: stats["level"] >= 5,
    },
    {
        "id": "level_10",
        "name": "Experienced",
        "description": "Reach level 10",
        "icon": "🌟",
        "requirement": "Level 10",
        "rarity": "rare",
        "check": lambda stats: stats["level"] >= 10,
    },
    {
        "id": "level_25",
        "name": "Veteran",
        "description": "Reach level 25",
        "icon": "✨",
        "requirement": "Level 25",
        "rarity": "epic",
        "check": lambda stats: stats["level"] >= 25,
    },
    # Time-of-day badges (synced with shared package)
    {
        "id": "early-bird",  # Matches shared package
        "name": "Early Bird",
        "description": "Study before 7 AM for 5 days",
        "icon": "🌅",
        "requirement": "5 early sessions",
        "rarity": "rare",
        "check": lambda stats: stats["early_sessions"] >= 5,
    },
    {
        "id": "night-owl",  # Matches shared package
        "name": "Night Owl",
        "description": "Study after 11 PM for 5 days",
        "icon": "🦉",
        "requirement": "5 late sessions",
        "rarity": "rare",
        "check": lambda stats: stats["late_sessions"] >= 5,
    },
]


async def check_and_award_badges(user_id: UUID, db: Session) -> List[Badge]:
    """
    Check badge eligibility and award any earned badges.
    
    Returns list of newly awarded badges.
    """
    from sqlalchemy import func

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    # Get user's current badges
    existing_badges = {
        ub.badge_id
        for ub in db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
    }

    # Calculate user stats for badge checking
    session_count = db.query(SessionModel).filter(SessionModel.user_id == user_id).count()

    total_duration = (
        db.query(func.sum(SessionModel.duration))
        .filter(SessionModel.user_id == user_id)
        .scalar()
    ) or 0

    max_productivity = (
        db.query(func.max(SessionModel.productivity_score))
        .filter(SessionModel.user_id == user_id)
        .scalar()
    ) or 0

    highest_focus_score = (
        db.query(func.max(SessionModel.focus_score))
        .filter(SessionModel.user_id == user_id)
        .scalar()
    ) or 0

    # Count early and late sessions
    early_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == user_id,
            func.extract("hour", SessionModel.start_time) < 7,
        )
        .count()
    )

    late_sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == user_id,
            func.extract("hour", SessionModel.start_time) >= 23,
        )
        .count()
    )

    stats = {
        "total_sessions": session_count,
        "total_hours": total_duration / 3600,
        "streak": user.streak,
        "level": user.level,
        "max_productivity": max_productivity,
        "highest_focus_score": highest_focus_score,
        "early_sessions": early_sessions,
        "late_sessions": late_sessions,
    }

    # Check each badge
    new_badges = []
    for badge_def in BADGE_DEFINITIONS:
        badge_id = badge_def["id"]

        # Skip if already earned
        if badge_id in existing_badges:
            continue

        # Check if eligible
        try:
            if badge_def["check"](stats):
                # Award badge
                badge = ensure_badge_exists(badge_def, db)
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge_id,
                )
                db.add(user_badge)

                # Create activity
                activity = Activity(
                    user_id=user_id,
                    user_name=user.display_name or user.email,
                    user_photo=user.photo_url,
                    type="badge_earned",
                    badge_id=badge_id,
                    badge_name=badge_def["name"],
                )
                db.add(activity)

                new_badges.append(badge)
                logger.info("Badge awarded", user_id=str(user_id), badge_id=badge_id)

        except Exception as e:
            logger.error("Badge check failed", badge_id=badge_id, error=str(e))

    if new_badges:
        db.commit()

    return new_badges


def ensure_badge_exists(badge_def: dict, db: Session) -> Badge:
    """Ensure badge exists in database, create if not."""
    badge = db.query(Badge).filter(Badge.id == badge_def["id"]).first()

    if not badge:
        badge = Badge(
            id=badge_def["id"],
            name=badge_def["name"],
            description=badge_def["description"],
            icon=badge_def["icon"],
            requirement=badge_def["requirement"],
            rarity=badge_def["rarity"],
        )
        db.add(badge)
        db.flush()

    return badge


def seed_badges(db: Session) -> int:
    """Seed all badge definitions into database."""
    created = 0
    for badge_def in BADGE_DEFINITIONS:
        existing = db.query(Badge).filter(Badge.id == badge_def["id"]).first()
        if not existing:
            badge = Badge(
                id=badge_def["id"],
                name=badge_def["name"],
                description=badge_def["description"],
                icon=badge_def["icon"],
                requirement=badge_def["requirement"],
                rarity=badge_def["rarity"],
            )
            db.add(badge)
            created += 1

    db.commit()
    return created
