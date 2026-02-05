"""Firebase Auth token verification middleware."""

from typing import Optional

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User

logger = structlog.get_logger()
settings = get_settings()

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)

# Firebase Admin SDK initialization (lazy)
_firebase_app = None


def get_firebase_app():
    """Get or initialize Firebase Admin app."""
    global _firebase_app
    if _firebase_app is None:
        import firebase_admin
        from firebase_admin import credentials
        import os
        from pathlib import Path

        # Determine credentials path
        cred_path = settings.firebase_credentials_path
        
        # If path is set but file doesn't exist, or if not set, try to auto-detect
        backend_dir = Path(__file__).parent.parent.parent
        
        if cred_path:
            # Resolve relative paths
            if not os.path.isabs(cred_path):
                cred_path = str(backend_dir / cred_path.lstrip('./'))
            
            # If the specified file doesn't exist, fall back to auto-detection
            if not os.path.exists(cred_path):
                logger.warning(
                    "Firebase credentials file not found at specified path, trying auto-detection",
                    specified_path=cred_path
                )
                cred_path = None
        
        # Auto-detect if not set or file doesn't exist
        if not cred_path:
            # Look for Firebase credentials JSON files
            possible_files = [
                backend_dir / "dann-91ae4-firebase-adminsdk-fbsvc-c517cef228.json",
                backend_dir / "service-account.json",
            ]
            
            for file_path in possible_files:
                if file_path.exists():
                    cred_path = str(file_path)
                    logger.info("Auto-detected Firebase credentials", path=cred_path)
                    break
        
        if cred_path:
            if not os.path.exists(cred_path):
                logger.error(
                    "Firebase credentials file not found",
                    path=cred_path,
                    cwd=os.getcwd(),
                    backend_dir=str(backend_dir)
                )
                raise FileNotFoundError(
                    f"Firebase credentials file not found: {cred_path}. "
                    f"Set FIREBASE_CREDENTIALS_PATH in .env or place credentials file in backend_fastapi/ directory."
                )
            cred = credentials.Certificate(cred_path)
        else:
            # Use application default credentials
            logger.info("Using application default credentials for Firebase")
            cred = credentials.ApplicationDefault()

        _firebase_app = firebase_admin.initialize_app(cred, {
            "projectId": settings.firebase_project_id or "dann-91ae4",
        })

    return _firebase_app


async def verify_firebase_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Verify Firebase ID token from Authorization header.
    
    Returns decoded token data with user info.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        from firebase_admin import auth

        # Initialize Firebase if needed
        get_firebase_app()

        # Verify the token
        decoded_token = auth.verify_id_token(token)

        return decoded_token

    except auth.InvalidIdTokenError as e:
        logger.warning("Invalid Firebase token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Firebase token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from the database.
    
    Creates user if they don't exist yet.
    """
    firebase_uid = token_data["uid"]

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        # Auto-create user on first authentication
        user = User(
            firebase_uid=firebase_uid,
            email=token_data.get("email", f"{firebase_uid}@firebase.user"),
            display_name=token_data.get("name"),
            photo_url=token_data.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created new user", user_id=str(user.id), email=user.email)

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    
    Use for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    try:
        token_data = await verify_firebase_token(credentials)
        return await get_current_user(token_data, db)
    except HTTPException:
        return None


async def require_admin(
    current_user: User = Depends(get_current_user),
    token_data: dict = Depends(verify_firebase_token),
) -> User:
    """
    Require admin role for protected endpoints.
    
    Checks for 'admin' custom claim in Firebase token.
    """
    # Check for admin custom claim
    is_admin = token_data.get("admin", False)

    # Also check email domain for backup admin access
    admin_emails = ["admin@dan.app"]  # Configure as needed
    is_admin_email = current_user.email in admin_emails

    if not (is_admin or is_admin_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
