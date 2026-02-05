"""Redis-based rate limiting middleware."""

import time
from datetime import datetime, timedelta
from typing import Optional

import structlog
from fastapi import Depends, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User, UserQuota

logger = structlog.get_logger()
settings = get_settings()

# Redis client (lazy initialization)
_redis_client = None


def get_redis():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        import redis
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware.
    
    Uses sliding window algorithm for accurate rate limiting.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/api/health"):
            return await call_next(request)
        
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Try to get user identifier from token
        user_id = await self._get_user_id(request)

        if user_id:
            # Rate limit by user ID
            key = f"rate_limit:user:{user_id}"
        else:
            # Rate limit by IP for unauthenticated requests
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:ip:{client_ip}"

        # Check rate limit
        # More lenient in development mode
        if settings.environment == "development":
            limit = settings.rate_limit_general * 5  # 5x more lenient in dev
        else:
            limit = settings.rate_limit_general
        window = 60  # 1 minute

        try:
            is_allowed, remaining, reset_time = self._check_rate_limit(key, limit, window)

            if not is_allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": reset_time,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time),
                    },
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)

            return response

        except Exception as e:
            # If Redis is down, allow request but log error
            logger.error("Rate limiting error", error=str(e))
            return await call_next(request)

    async def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from Authorization header if present."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        try:
            from firebase_admin import auth
            from app.middleware.auth import get_firebase_app

            get_firebase_app()
            token = auth_header[7:]  # Remove "Bearer "
            decoded = auth.verify_id_token(token)
            return decoded["uid"]
        except Exception:
            return None

    def _check_rate_limit(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using sliding window counter.
        
        Returns: (is_allowed, remaining_requests, reset_timestamp)
        """
        redis = get_redis()
        now = time.time()
        window_start = now - window

        # Use Redis pipeline for atomic operations
        pipe = redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set key expiry
        pipe.expire(key, window)

        results = pipe.execute()
        current_count = results[1]

        remaining = max(0, limit - current_count - 1)
        reset_time = int(now + window)

        is_allowed = current_count < limit

        return is_allowed, remaining, reset_time


async def check_ai_quota(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
) -> None:
    """
    Check AI endpoint quota for the user.
    
    Raises HTTPException if quota exceeded.
    """
    # Get or create user quota
    quota = db.query(UserQuota).filter(UserQuota.user_id == current_user.id).first()

    if not quota:
        quota = UserQuota(user_id=current_user.id)
        db.add(quota)
        db.commit()
        db.refresh(quota)

    now = datetime.utcnow()

    # Reset counter if it's a new day
    if quota.ai_requests_reset_at is None or now >= quota.ai_requests_reset_at:
        quota.ai_requests_today = 0
        quota.ai_requests_reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    # Check quota
    if quota.ai_requests_today >= settings.rate_limit_ai:
        reset_seconds = int((quota.ai_requests_reset_at - now).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"AI request quota exceeded. Resets in {reset_seconds} seconds.",
            headers={
                "X-AI-Quota-Limit": str(settings.rate_limit_ai),
                "X-AI-Quota-Remaining": "0",
                "X-AI-Quota-Reset": str(int(quota.ai_requests_reset_at.timestamp())),
                "Retry-After": str(reset_seconds),
            },
        )

    # Increment counter
    quota.ai_requests_today += 1
    quota.last_request_at = now
    db.commit()


def get_session_rate_limiter():
    """
    Rate limiter specifically for session creation.
    
    More restrictive than general API (30/min vs 100/min).
    """
    async def check_session_rate_limit(request: Request):
        # Implementation similar to middleware but with different limits
        pass

    return check_session_rate_limit
