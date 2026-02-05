"""User management endpoints with privacy checks."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User, UserStats
from app.models.social import Friend
from app.schemas.user import UserResponse, UserUpdate, UserPublicResponse, UserStatsResponse

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user profile with privacy checks."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If requesting own profile, return full data
    if user.id == current_user.id:
        return user

    # Check if user is public
    if not user.is_public:
        # Check if they are friends
        is_friend = (
            db.query(Friend)
            .filter(
                Friend.user_id == current_user.id,
                Friend.friend_user_id == user_id,
            )
            .first()
        )

        if not is_friend:
            raise HTTPException(
                status_code=403,
                detail="This user's profile is private",
            )

    return user


@router.get("/{user_id}/public", response_model=UserPublicResponse)
async def get_user_public(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Get public user information (no auth required)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only return public fields
    return UserPublicResponse(
        id=user.id,
        display_name=user.display_name,
        username=user.username,
        photo_url=user.photo_url if user.is_public else None,
        level=user.level if user.is_public else None,
        is_public=user.is_public,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user profile."""
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Can only update your own profile",
        )

    # Check username uniqueness if being updated
    if user_update.username:
        existing = (
            db.query(User)
            .filter(User.username == user_update.username, User.id != user_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Username already taken",
            )

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    from datetime import datetime
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user statistics."""
    # Privacy check
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id != current_user.id and not user.is_public:
        is_friend = (
            db.query(Friend)
            .filter(
                Friend.user_id == current_user.id,
                Friend.friend_user_id == user_id,
            )
            .first()
        )
        if not is_friend:
            raise HTTPException(
                status_code=403,
                detail="This user's stats are private",
            )

    stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()

    if not stats:
        # Return default stats if none exist
        return UserStatsResponse(
            user_id=user_id,
            total_sessions=0,
            total_hours=0,
            average_focus_score=0,
            average_productivity_score=0,
            topic_distribution={},
            study_heatmap={},
            weekly_trend=[],
        )

    return stats


@router.get("/search/")
async def search_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, max_length=50),
    limit: int = Query(10, ge=1, le=50),
):
    """Search users by username or display name."""
    users = (
        db.query(User)
        .filter(
            User.is_public == True,
            User.id != current_user.id,
            (User.username.ilike(f"%{q}%") | User.display_name.ilike(f"%{q}%")),
        )
        .limit(limit)
        .all()
    )

    return [
        UserPublicResponse(
            id=u.id,
            display_name=u.display_name,
            username=u.username,
            photo_url=u.photo_url,
            level=u.level,
            is_public=u.is_public,
        )
        for u in users
    ]
