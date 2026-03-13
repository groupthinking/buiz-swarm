"""
Minimal Celery application for BuizSwarm background workers.

The upstream compose stack starts a Celery worker, so this module provides the
expected app entrypoint even before task routing is expanded further.
"""
from celery import Celery

from .config import settings


celery_app = Celery(
    "buizswarm",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Celery CLI looks for a module-level `app` by default.
app = celery_app


@celery_app.task(name="buizswarm.ping")
def ping() -> str:
    """Basic worker health task."""
    return "pong"
