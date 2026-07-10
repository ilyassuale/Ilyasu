"""Resume upload, parsing, and intelligence routes."""
from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import Job, Resume, User
from app.schemas.resume import JobMatchOut, ResumeIntelligenceOut, ResumeOut, ResumeSection, ResumeUploadOut
from app.services.job_matcher import match_jobs
from app.services.resume_intelligence import analyze_resume
from app.services.resume_parser import extract_text, parse_resume
from app.services.storage import download_file, upload_file

router = APIRouter(prefix="/resumes", tags=["Resumes"])


ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


@router.post("/upload", response_model=ResumeUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB.")

    key = upload_file(file_bytes, file.filename or "resume", file.content_type)
    resume = Resume(
        user_id=user.id,
        file_key=key,
        file_name=file.filename or "resume",
        mime_type=file.content_type,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return {"id": resume.id, "file_name": resume.file_name, "status": "uploaded"}


@router.post("/{resume_id}/parse", response_model=ResumeIntelligenceOut)
async def parse_resume_endpoint(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    start = time.time()
    try:
        file_bytes = download_file(resume.file_key)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Could not retrieve resume file from storage"
        ) from exc

    text = extract_text(file_bytes, resume.mime_type)

    parsed = parse_resume(text)
    resume.parsed_text = text
    resume.parsed_json = parsed.model_dump()

    intelligence = analyze_resume(parsed, text)
    resume.resume_score = intelligence.resume_score
    resume.ats_score = intelligence.ats_score
    resume.missing_skills = intelligence.missing_skills
    resume.grammar_issues = intelligence.grammar_issues
    resume.recommended_roles = intelligence.recommended_roles
    resume.strengths = intelligence.strengths
    resume.weaknesses = intelligence.weaknesses

    await db.commit()
    await db.refresh(resume)

    return {
        "resume_id": resume.id,
        "parsed": parsed,
        "intelligence": intelligence,
        "processing_time_ms": int((time.time() - start) * 1000),
    }


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Resume:
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.post("/{resume_id}/match", response_model=JobMatchOut)
async def match_resume_jobs(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JobMatchOut:
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    resume = result.scalar_one_or_none()
    if not resume or not resume.parsed_json:
        raise HTTPException(status_code=404, detail="Resume not found or not parsed")

    parsed = ResumeSection(**resume.parsed_json)
    jobs_result = await db.execute(select(Job).where(Job.is_active))
    jobs = jobs_result.scalars().all()
    job_dicts = [
        {
            "id": j.id,
            "title": j.title,
            "description": j.description,
            "required_skills": j.required_skills or [],
            "company": j.company.name if j.company else None,
        }
        for j in jobs
    ]

    return match_jobs(parsed, job_dicts, resume_id=resume.id)
