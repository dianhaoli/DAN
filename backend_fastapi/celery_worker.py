"""Celery worker entry point.

Run with:
    celery -A celery_worker.celery_app worker --loglevel=info --queues=ml,ai,stats
"""

from app.workers import celery_app

if __name__ == "__main__":
    celery_app.start()
