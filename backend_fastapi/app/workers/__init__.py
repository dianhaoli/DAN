"""Celery application configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "dan_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.ml_tasks",
        "app.workers.ai_tasks",
        "app.workers.stats_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=270,  # Soft limit at 4.5 minutes
    worker_prefetch_multiplier=1,  # One task at a time for ML tasks
    task_acks_late=True,  # Acknowledge after completion for reliability
    task_reject_on_worker_lost=True,
)

# Task routes - route ML tasks to dedicated queue
celery_app.conf.task_routes = {
    "app.workers.ml_tasks.*": {"queue": "ml"},
    "app.workers.ai_tasks.*": {"queue": "ai"},
    "app.workers.stats_tasks.*": {"queue": "stats"},
}
