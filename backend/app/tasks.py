"""Celery async tasks."""
from __future__ import annotations

from typing import Any

from app.celery import celery_app


@celery_app.task(bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def process_resume(self: Any, resume_id: str) -> dict[str, Any]:
    """Async resume parsing and scoring task."""
    return {"status": "queued", "resume_id": resume_id}


@celery_app.task(bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def generate_interview_questions(self: Any, session_id: str) -> dict[str, Any]:
    """Async interview question generation."""
    return {"status": "queued", "session_id": session_id}


@celery_app.task(bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def evaluate_interview(self: Any, session_id: str) -> dict[str, Any]:
    """Async final interview evaluation."""
    return {"status": "queued", "session_id": session_id}
