"""Celery tasks for async ML inference."""

from datetime import datetime

import structlog

from app.workers import celery_app
from app.database import SessionLocal
from app.models.session import Session
from app.ml.inference import process_session_ml
from app.ml.loader import get_model_version, models_ready

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_session_ml_task(self, session_id: str) -> dict:
    """
    Process ML inference for a session asynchronously.
    
    This task:
    1. Loads session data from database
    2. Runs DistilBERT classification
    3. Runs XGBoost productivity prediction
    4. Updates session with ML results
    
    Args:
        session_id: UUID of the session to process
        
    Returns:
        Dictionary with ML results
    """
    logger.info("Starting ML processing", session_id=session_id, task_id=self.request.id)

    db = SessionLocal()
    try:
        # Get session
        session = db.query(Session).filter(Session.id == session_id).first()

        if not session:
            logger.error("Session not found", session_id=session_id)
            return {"error": "Session not found"}

        # Update status to processing
        session.processing_status = "processing"
        db.commit()

        # Check if models are ready
        if not models_ready():
            logger.warning("ML models not ready, using defaults")
            session.processing_status = "completed"
            session.activity_label = "study"
            session.productivity_score = 50
            session.focus_score = 0.5
            session.ml_model_version = "none"
            session.ml_processed_at = datetime.utcnow()
            db.commit()
            return {"status": "completed", "used_defaults": True}

        # Run ML pipeline synchronously (we're in a worker thread)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            ml_results = loop.run_until_complete(
                process_session_ml(
                    domains=session.domains or [],
                    clicks=session.clicks or 0,
                    keystrokes=session.keystrokes or 0,
                    duration=session.duration,
                )
            )
        finally:
            loop.close()

        # Update session with results
        session.activity_label = ml_results["activity_label"]
        session.productivity_score = ml_results["productivity_score"]
        session.focus_score = ml_results["focus_score"]
        session.ml_model_version = ml_results["ml_model_version"]
        session.ml_features = ml_results["ml_features"]
        session.ml_processed_at = datetime.utcnow()
        session.processing_status = "completed"

        # Calculate and award XP based on productivity
        xp_earned = calculate_session_xp(
            duration=session.duration,
            productivity_score=ml_results["productivity_score"],
            activity_label=ml_results["activity_label"],
        )
        session.xp_earned = xp_earned

        db.commit()

        logger.info(
            "ML processing completed",
            session_id=session_id,
            productivity_score=ml_results["productivity_score"],
            activity_label=ml_results["activity_label"],
            xp_earned=xp_earned,
        )

        # Trigger user stats update
        update_user_after_session.delay(str(session.user_id), session_id, xp_earned)

        return {
            "status": "completed",
            "session_id": session_id,
            **ml_results,
            "xp_earned": xp_earned,
        }

    except Exception as e:
        logger.error("ML processing failed", session_id=session_id, error=str(e))
        
        # Mark as failed
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            if session:
                session.processing_status = "failed"
                db.commit()
        except Exception:
            pass

        raise

    finally:
        db.close()


# Alias for the API to use
process_session_ml = process_session_ml_task


@celery_app.task(bind=True)
def update_user_after_session(self, user_id: str, session_id: str, xp_earned: int) -> dict:
    """
    Update user stats after session completion.
    
    This task:
    1. Awards XP to user
    2. Checks for level up
    3. Updates streak
    4. Creates activity feed entry
    """
    from app.models.user import User
    from app.models.social import Activity

    logger.info("Updating user after session", user_id=user_id, xp_earned=xp_earned)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        session = db.query(Session).filter(Session.id == session_id).first()

        if not user or not session:
            return {"error": "User or session not found"}

        # Award XP
        old_level = user.level
        user.xp += xp_earned

        # Check level up
        import math
        new_level = int(math.sqrt(user.xp / 100))
        leveled_up = new_level > old_level
        if leveled_up:
            user.level = new_level

        # Update total study time
        user.total_study_time += session.duration // 60  # Convert to minutes

        # Update streak
        from datetime import timedelta
        today = datetime.utcnow().date()
        
        # Get last session before this one
        last_session = (
            db.query(Session)
            .filter(
                Session.user_id == user_id,
                Session.id != session_id,
            )
            .order_by(Session.created_at.desc())
            .first()
        )

        if last_session:
            last_date = last_session.created_at.date()
            days_diff = (today - last_date).days

            if days_diff == 0:
                # Same day, streak continues
                pass
            elif days_diff == 1:
                # Next day, increment streak
                user.streak += 1
            else:
                # Gap, reset streak
                user.streak = 1
        else:
            # First session
            user.streak = 1

        # Update longest streak
        if user.streak > user.longest_streak:
            user.longest_streak = user.streak

        db.commit()

        # Create activity for session completion
        activity = Activity(
            user_id=user.id,
            user_name=user.display_name or user.email,
            user_photo=user.photo_url,
            type="session_complete",
            session_id=session.id,
            topic=session.topic,
            duration=session.duration,
            xp_earned=xp_earned,
        )
        db.add(activity)

        # Create level up activity if applicable
        if leveled_up:
            level_activity = Activity(
                user_id=user.id,
                user_name=user.display_name or user.email,
                user_photo=user.photo_url,
                type="level_up",
                new_level=new_level,
            )
            db.add(level_activity)

        db.commit()

        return {
            "status": "completed",
            "xp_awarded": xp_earned,
            "new_level": new_level if leveled_up else None,
            "streak": user.streak,
        }

    except Exception as e:
        logger.error("User update failed", user_id=user_id, error=str(e))
        raise

    finally:
        db.close()


def calculate_session_xp(
    duration: int,
    productivity_score: int,
    activity_label: str,
) -> int:
    """
    Calculate XP earned from a session.
    
    Formula:
    - Base: 1 XP per minute
    - Productivity multiplier: 0.5x to 1.5x based on score
    - Activity bonus: +20% for study, +10% for research, -30% for distraction
    """
    # Base XP (1 per minute, capped at 120)
    minutes = min(duration // 60, 120)
    base_xp = minutes

    # Productivity multiplier (50 score = 1x, 100 = 1.5x, 0 = 0.5x)
    productivity_mult = 0.5 + (productivity_score / 100)

    # Activity multiplier
    activity_mults = {
        "study": 1.2,
        "research": 1.1,
        "distraction": 0.7,
    }
    activity_mult = activity_mults.get(activity_label, 1.0)

    # Calculate final XP
    xp = int(base_xp * productivity_mult * activity_mult)

    return max(1, xp)  # Minimum 1 XP
