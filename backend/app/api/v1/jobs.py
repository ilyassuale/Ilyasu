"""Job listing management routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, get_current_user
from app.db.session import get_db
from app.models.models import Company, Job, User

router = APIRouter(prefix="/jobs", tags=["Jobs"])

require_job_editor = RoleChecker(["recruiter", "admin"])


@router.get("/")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    result = await db.execute(
        select(Job, Company).join(Company, isouter=True).where(Job.is_active).offset(skip).limit(limit)
    )
    rows = result.all()
    return {
        "items": [
            {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "required_skills": job.required_skills,
                "preferred_skills": job.preferred_skills,
                "company": company.name if company else None,
                "location": job.location,
                "employment_type": job.employment_type,
            }
            for job, company in rows
        ]
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_job_editor),
) -> dict[str, Any]:
    job = Job(
        title=payload["title"],
        description=payload["description"],
        required_skills=payload.get("required_skills", []),
        preferred_skills=payload.get("preferred_skills", []),
        company_id=payload.get("company_id"),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return {"id": job.id, "title": job.title}
