"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, verify_firebase_token
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate

router = APIRouter()


@router.post("/verify")
async def verify_token(
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db),
):
    """Verify Firebase ID token and return/create user."""
    firebase_uid = token_data["uid"]
    email = token_data.get("email")
    name = token_data.get("name", "")
    picture = token_data.get("picture")

    # Find or create user
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=name,
            photo_url=picture,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "user_id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "is_new": user.created_at == user.updated_at,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user's information."""
    return current_user
