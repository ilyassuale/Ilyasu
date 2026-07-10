"""Recruiter dashboard routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker
from app.db.session import get_db
from app.models.models import InterviewSession, Report, Resume, User

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


require_recruiter = RoleChecker(["recruiter", "admin"])


@router.get("/candidates")
async def search_candidates(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_recruiter),
) -> dict[str, Any]:
    stmt = select(User).where(User.role == "candidate").join(Resume, isouter=True)
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    users = result.scalars().all()
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "resume_score": u.resumes[0].resume_score if u.resumes else None,
            }
            for u in users
        ]
    }


@router.get("/reports")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_recruiter),
    skip: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    result = await db.execute(
        select(Report, User, InterviewSession)
        .join(User, Report.user_id == User.id)
        .join(InterviewSession, Report.session_id == InterviewSession.id)
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()
    return {
        "items": [
            {
                "report_id": report.id,
                "candidate": user.email,
                "session_id": session.id,
                "overall_score": report.overall_score,
                "created_at": report.created_at,
            }
            for report, user, session in rows
        ]
    }


@router.get("/analytics")
async def recruiter_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_recruiter),
) -> dict[str, Any]:
    total_candidates = await db.execute(select(func.count(User.id)).where(User.role == "candidate"))
    total_sessions = await db.execute(select(func.count(InterviewSession.id)))
    total_reports = await db.execute(select(func.count(Report.id)))
    avg_score = await db.execute(select(func.avg(Report.overall_score)))
    return {
        "total_candidates": total_candidates.scalar(),
        "total_sessions": total_sessions.scalar(),
        "total_reports": total_reports.scalar(),
        "average_overall_score": float(avg_score.scalar() or 0),
    }
