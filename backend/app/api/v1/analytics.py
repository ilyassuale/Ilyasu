"""Candidate-facing analytics routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import InterviewSession, Report, User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def candidate_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    sessions_count = await db.execute(
        select(func.count(InterviewSession.id)).where(InterviewSession.user_id == user.id)
    )
    reports = await db.execute(
        select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc())
    )
    report_list = reports.scalars().all()
    avg_score = await db.execute(
        select(func.avg(Report.overall_score)).where(Report.user_id == user.id)
    )

    return {
        "total_sessions": sessions_count.scalar(),
        "average_overall_score": float(avg_score.scalar() or 0),
        "recent_reports": [
            {
                "session_id": r.session_id,
                "overall_score": r.overall_score,
                "created_at": r.created_at,
                "strengths": r.strengths,
                "weaknesses": r.weaknesses,
            }
            for r in report_list
        ],
        "performance_trend": [
            {"date": r.created_at.isoformat(), "score": r.overall_score} for r in report_list
        ],
    }


@router.get("/skill-trends")
async def skill_trends(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    # Aggregate missing skills from resumes
    from app.models.models import Resume

    resumes = await db.execute(select(Resume).where(Resume.user_id == user.id))
    skill_counts: dict[str, int] = {}
    for r in resumes.scalars().all():
        for skill in r.missing_skills or []:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    return {"missing_skills": skill_counts}
