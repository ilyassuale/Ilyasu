"""Celery configuration for async AI tasks."""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "interview_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
