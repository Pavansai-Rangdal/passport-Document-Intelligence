"""Celery background workers."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "passport_workers",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_time_limit=settings.processing_timeout_seconds,
    beat_schedule={
        "retention-cleanup-daily": {
            "task": "run_retention_cleanup",
            "schedule": 86400,  # every 24 hours
        },
    },
)
