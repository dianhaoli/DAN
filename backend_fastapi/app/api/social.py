"""Social features: friends, activities, using junction table."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.social import Friend, FriendRequest, Activity
from app.schemas.social import (
    FriendRequestCreate,
    FriendRequestResponse,
    FriendResponse,
    ActivityResponse,
    ReactionCreate,
)

router = APIRouter()


# ============ Friend Requests ============

@router.post("/friends/request", response_model=FriendRequestResponse)
async def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a friend request to another user."""
    to_user_id = request_data.to_user_id

    if to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")

    # Check if user exists
    to_user = db.query(User).filter(User.id == to_user_id).first()
    if not to_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already friends
    existing_friendship = (
        db.query(Friend)
        .filter(
            Friend.user_id == current_user.id,
            Friend.friend_user_id == to_user_id,
        )
        .first()
    )
    if existing_friendship:
        raise HTTPException(status_code=400, detail="Already friends with this user")

    # Check for existing request
    existing_request = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.from_user_id == current_user.id,
            FriendRequest.to_user_id == to_user_id,
            FriendRequest.status == "pending",
        )
        .first()
    )
    if existing_request:
        raise HTTPException(status_code=400, detail="Friend request already sent")

    # Check if they sent us a request (auto-accept)
    incoming_request = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.from_user_id == to_user_id,
            FriendRequest.to_user_id == current_user.id,
            FriendRequest.status == "pending",
        )
        .first()
    )
    if incoming_request:
        # Auto-accept mutual request
        return await accept_friend_request(incoming_request.id, current_user, db)

    # Create new request
    friend_request = FriendRequest(
        from_user_id=current_user.id,
        to_user_id=to_user_id,
    )
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)

    return friend_request


@router.get("/friends/requests", response_model=List[FriendRequestResponse])
async def get_friend_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    direction: str = Query("incoming", regex="^(incoming|outgoing)$"),
):
    """Get friend requests (incoming or outgoing)."""
    if direction == "incoming":
        requests = (
            db.query(FriendRequest)
            .filter(
                FriendRequest.to_user_id == current_user.id,
                FriendRequest.status == "pending",
            )
            .all()
        )
    else:
        requests = (
            db.query(FriendRequest)
            .filter(
                FriendRequest.from_user_id == current_user.id,
                FriendRequest.status == "pending",
            )
            .all()
        )

    return requests


@router.post("/friends/requests/{request_id}/accept", response_model=FriendRequestResponse)
async def accept_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept a friend request."""
    friend_request = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.id == request_id,
            FriendRequest.to_user_id == current_user.id,
            FriendRequest.status == "pending",
        )
        .first()
    )

    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    # Update request status
    friend_request.status = "accepted"
    friend_request.updated_at = datetime.utcnow()

    # Create bidirectional friendship in junction table
    friendship1 = Friend(
        user_id=current_user.id,
        friend_user_id=friend_request.from_user_id,
    )
    friendship2 = Friend(
        user_id=friend_request.from_user_id,
        friend_user_id=current_user.id,
    )

    db.add(friendship1)
    db.add(friendship2)
    db.commit()
    db.refresh(friend_request)

    return friend_request


@router.post("/friends/requests/{request_id}/reject", response_model=FriendRequestResponse)
async def reject_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reject a friend request."""
    friend_request = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.id == request_id,
            FriendRequest.to_user_id == current_user.id,
            FriendRequest.status == "pending",
        )
        .first()
    )

    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    friend_request.status = "rejected"
    friend_request.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(friend_request)

    return friend_request


# ============ Friends ============

@router.get("/friends", response_model=List[FriendResponse])
async def list_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all friends using junction table."""
    friendships = (
        db.query(Friend, User)
        .join(User, Friend.friend_user_id == User.id)
        .filter(Friend.user_id == current_user.id)
        .all()
    )

    return [
        FriendResponse(
            user_id=user.id,
            display_name=user.display_name,
            username=user.username,
            photo_url=user.photo_url,
            level=user.level,
            friends_since=friendship.created_at,
        )
        for friendship, user in friendships
    ]


@router.delete("/friends/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a friend (removes bidirectional relationship)."""
    # Delete both directions of friendship
    db.query(Friend).filter(
        Friend.user_id == current_user.id,
        Friend.friend_user_id == user_id,
    ).delete()

    db.query(Friend).filter(
        Friend.user_id == user_id,
        Friend.friend_user_id == current_user.id,
    ).delete()

    db.commit()


# ============ Activities ============

@router.get("/activities", response_model=List[ActivityResponse])
async def get_activity_feed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get activity feed from friends."""
    # Get friend IDs
    friend_ids = (
        db.query(Friend.friend_user_id)
        .filter(Friend.user_id == current_user.id)
        .subquery()
    )

    activities = (
        db.query(Activity)
        .filter(Activity.user_id.in_(friend_ids))
        .order_by(Activity.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return activities


@router.post("/activities/{activity_id}/react")
async def react_to_activity(
    activity_id: UUID,
    reaction: ReactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a reaction to an activity."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Update reactions JSONB
    reactions = activity.reactions or {}
    emoji = reaction.emoji

    if emoji not in reactions:
        reactions[emoji] = []

    user_id_str = str(current_user.id)
    if user_id_str not in reactions[emoji]:
        reactions[emoji].append(user_id_str)
    else:
        # Toggle off if already reacted
        reactions[emoji].remove(user_id_str)
        if not reactions[emoji]:
            del reactions[emoji]

    activity.reactions = reactions
    db.commit()

    return {"reactions": reactions}
