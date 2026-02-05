"""Celery tasks for statistics aggregation and leaderboard updates."""

from datetime import datetime, timedelta

import structlog

from app.workers import celery_app
from app.database import SessionLocal

logger = structlog.get_logger()


@celery_app.task(bind=True)
def update_leaderboards(self) -> dict:
    """
    Update all leaderboards.
    
    This task recalculates leaderboard rankings for:
    - Hours studied (daily, weekly, monthly, all-time)
    - XP earned
    - Productivity scores
    - Streaks
    """
    from sqlalchemy import func, desc
    from app.models.user import User
    from app.models.session import Session
    from app.models.gamification import Leaderboard

    logger.info("Starting leaderboard update")

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        leaderboards_updated = 0

        # Hours leaderboards by period
        periods = {
            "daily": today_start,
            "weekly": week_start,
            "monthly": month_start,
            "all-time": None,
        }

        for period_name, period_start in periods.items():
            # Build query for hours
            query = (
                db.query(
                    User.id,
                    User.display_name,
                    User.photo_url,
                    func.sum(Session.duration).label("total_seconds"),
                )
                .join(Session, Session.user_id == User.id)
                .filter(User.is_public == True)
            )

            if period_start:
                query = query.filter(Session.created_at >= period_start)

            results = (
                query.group_by(User.id, User.display_name, User.photo_url)
                .order_by(desc("total_seconds"))
                .limit(100)
                .all()
            )

            entries = [
                {
                    "user_id": str(r.id),
                    "display_name": r.display_name or "Anonymous",
                    "photo_url": r.photo_url,
                    "value": round((r.total_seconds or 0) / 3600, 2),  # Convert to hours
                    "rank": i + 1,
                }
                for i, r in enumerate(results)
            ]

            # Update or create leaderboard
            leaderboard_id = f"hours-{period_name}-global"
            leaderboard = db.query(Leaderboard).filter(Leaderboard.id == leaderboard_id).first()

            if not leaderboard:
                leaderboard = Leaderboard(
                    id=leaderboard_id,
                    name=f"Study Hours ({period_name.title()})",
                    type="hours",
                    period=period_name,
                    scope="global",
                )
                db.add(leaderboard)

            leaderboard.entries = entries
            leaderboard.updated_at = now
            leaderboards_updated += 1

        # XP leaderboard (all-time only)
        xp_results = (
            db.query(User)
            .filter(User.is_public == True)
            .order_by(desc(User.xp))
            .limit(100)
            .all()
        )

        xp_entries = [
            {
                "user_id": str(u.id),
                "display_name": u.display_name or "Anonymous",
                "photo_url": u.photo_url,
                "value": u.xp,
                "rank": i + 1,
            }
            for i, u in enumerate(xp_results)
        ]

        xp_leaderboard = db.query(Leaderboard).filter(Leaderboard.id == "xp-all-time-global").first()
        if not xp_leaderboard:
            xp_leaderboard = Leaderboard(
                id="xp-all-time-global",
                name="Total XP",
                type="xp",
                period="all-time",
                scope="global",
            )
            db.add(xp_leaderboard)

        xp_leaderboard.entries = xp_entries
        xp_leaderboard.updated_at = now
        leaderboards_updated += 1

        # Streak leaderboard
        streak_results = (
            db.query(User)
            .filter(User.is_public == True, User.streak > 0)
            .order_by(desc(User.streak))
            .limit(100)
            .all()
        )

        streak_entries = [
            {
                "user_id": str(u.id),
                "display_name": u.display_name or "Anonymous",
                "photo_url": u.photo_url,
                "value": u.streak,
                "rank": i + 1,
            }
            for i, u in enumerate(streak_results)
        ]

        streak_leaderboard = db.query(Leaderboard).filter(Leaderboard.id == "streak-all-time-global").first()
        if not streak_leaderboard:
            streak_leaderboard = Leaderboard(
                id="streak-all-time-global",
                name="Current Streak",
                type="streak",
                period="all-time",
                scope="global",
            )
            db.add(streak_leaderboard)

        streak_leaderboard.entries = streak_entries
        streak_leaderboard.updated_at = now
        leaderboards_updated += 1

        # Productivity leaderboard (weekly)
        productivity_results = (
            db.query(
                User.id,
                User.display_name,
                User.photo_url,
                func.avg(Session.productivity_score).label("avg_productivity"),
            )
            .join(Session, Session.user_id == User.id)
            .filter(
                User.is_public == True,
                Session.created_at >= week_start,
                Session.productivity_score.isnot(None),
            )
            .group_by(User.id, User.display_name, User.photo_url)
            .having(func.count(Session.id) >= 3)  # Minimum 3 sessions
            .order_by(desc("avg_productivity"))
            .limit(100)
            .all()
        )

        productivity_entries = [
            {
                "user_id": str(r.id),
                "display_name": r.display_name or "Anonymous",
                "photo_url": r.photo_url,
                "value": round(float(r.avg_productivity), 1),
                "rank": i + 1,
            }
            for i, r in enumerate(productivity_results)
        ]

        productivity_leaderboard = db.query(Leaderboard).filter(
            Leaderboard.id == "productivity-weekly-global"
        ).first()
        if not productivity_leaderboard:
            productivity_leaderboard = Leaderboard(
                id="productivity-weekly-global",
                name="Productivity Score (Weekly)",
                type="productivity",
                period="weekly",
                scope="global",
            )
            db.add(productivity_leaderboard)

        productivity_leaderboard.entries = productivity_entries
        productivity_leaderboard.updated_at = now
        leaderboards_updated += 1

        db.commit()

        logger.info("Leaderboards updated", count=leaderboards_updated)

        return {
            "status": "completed",
            "leaderboards_updated": leaderboards_updated,
        }

    except Exception as e:
        logger.error("Leaderboard update failed", error=str(e))
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(bind=True)
def update_user_stats(self, user_id: str) -> dict:
    """
    Update aggregated stats for a user.
    
    This task should only be called from background jobs,
    never from API endpoints directly.
    """
    from sqlalchemy import func
    from app.models.user import User, UserStats
    from app.models.session import Session

    logger.info("Updating user stats", user_id=user_id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}

        # Get or create stats record
        stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()
        if not stats:
            stats = UserStats(user_id=user.id)
            db.add(stats)

        # Calculate aggregates
        session_stats = (
            db.query(
                func.count(Session.id).label("total_sessions"),
                func.sum(Session.duration).label("total_seconds"),
                func.avg(Session.focus_score).label("avg_focus"),
                func.avg(Session.productivity_score).label("avg_productivity"),
            )
            .filter(Session.user_id == user_id)
            .first()
        )

        stats.total_sessions = session_stats.total_sessions or 0
        stats.total_hours = round((session_stats.total_seconds or 0) / 3600, 2)
        stats.average_focus_score = round(float(session_stats.avg_focus or 0), 2)
        stats.average_productivity_score = int(session_stats.avg_productivity or 0)

        # Calculate topic distribution
        topic_results = (
            db.query(
                Session.topic,
                func.sum(Session.duration).label("total_seconds"),
            )
            .filter(Session.user_id == user_id)
            .group_by(Session.topic)
            .all()
        )
        stats.topic_distribution = {
            r.topic: r.total_seconds // 60 for r in topic_results
        }

        # Calculate study heatmap (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        heatmap_results = (
            db.query(
                func.date(Session.created_at).label("date"),
                func.sum(Session.duration).label("total_seconds"),
            )
            .filter(Session.user_id == user_id, Session.created_at >= thirty_days_ago)
            .group_by(func.date(Session.created_at))
            .all()
        )
        stats.study_heatmap = {
            str(r.date): r.total_seconds // 60 for r in heatmap_results
        }

        # Calculate weekly trend (last 12 weeks)
        weekly_trend = []
        for i in range(12):
            week_start = datetime.utcnow() - timedelta(weeks=i + 1)
            week_end = datetime.utcnow() - timedelta(weeks=i)

            week_total = (
                db.query(func.sum(Session.duration))
                .filter(
                    Session.user_id == user_id,
                    Session.created_at >= week_start,
                    Session.created_at < week_end,
                )
                .scalar()
            )
            weekly_trend.insert(0, (week_total or 0) // 60)

        stats.weekly_trend = weekly_trend

        db.commit()

        logger.info("User stats updated", user_id=user_id)

        return {"status": "completed", "user_id": user_id}

    except Exception as e:
        logger.error("User stats update failed", user_id=user_id, error=str(e))
        raise

    finally:
        db.close()


@celery_app.task(bind=True)
def generate_all_weekly_summaries(self) -> dict:
    """
    Generate weekly summaries for all users.
    
    Should be run weekly via celery beat (Sunday night).
    This task queues individual summary generation tasks for each user.
    """
    from app.models.user import User
    from app.workers.ai_tasks import generate_weekly_summary_task

    logger.info("Starting weekly summary generation for all users")

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        week_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get all active users (users with sessions in the past week)
        from app.models.session import Session
        
        active_user_ids = (
            db.query(Session.user_id)
            .filter(Session.created_at >= week_start)
            .distinct()
            .all()
        )

        queued_count = 0
        for (user_id,) in active_user_ids:
            # Queue individual summary generation
            generate_weekly_summary_task.delay(
                str(user_id),
                week_start.isoformat(),
                week_end.isoformat(),
            )
            queued_count += 1

        logger.info("Weekly summaries queued", count=queued_count)

        return {
            "status": "completed",
            "summaries_queued": queued_count,
        }

    except Exception as e:
        logger.error("Weekly summary generation failed", error=str(e))
        raise

    finally:
        db.close()


@celery_app.task(bind=True)
def reset_daily_streaks(self) -> dict:
    """
    Reset streaks for users who didn't study yesterday.
    
    Should be run daily via celery beat.
    """
    from app.models.user import User
    from app.models.session import Session

    logger.info("Checking and resetting streaks")

    db = SessionLocal()
    try:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())

        # Get users with active streaks
        users_with_streak = db.query(User).filter(User.streak > 0).all()

        reset_count = 0
        for user in users_with_streak:
            # Check if they studied yesterday
            session = (
                db.query(Session)
                .filter(
                    Session.user_id == user.id,
                    Session.created_at >= yesterday_start,
                    Session.created_at <= yesterday_end,
                )
                .first()
            )

            if not session:
                user.streak = 0
                reset_count += 1

        db.commit()

        logger.info("Streaks reset", count=reset_count)

        return {"status": "completed", "streaks_reset": reset_count}

    except Exception as e:
        logger.error("Streak reset failed", error=str(e))
        raise

    finally:
        db.close()


# Celery beat schedule for periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "update-leaderboards-hourly": {
        "task": "app.workers.stats_tasks.update_leaderboards",
        "schedule": 3600.0,  # Every hour
    },
    "reset-streaks-daily": {
        "task": "app.workers.stats_tasks.reset_daily_streaks",
        "schedule": crontab(hour=0, minute=30),  # Daily at 00:30 UTC
        },
    "generate-weekly-summaries": {
        "task": "app.workers.stats_tasks.generate_all_weekly_summaries",
        "schedule": crontab(hour=23, minute=59, day_of_week=0),  # Sunday 23:59 UTC
    },
}
