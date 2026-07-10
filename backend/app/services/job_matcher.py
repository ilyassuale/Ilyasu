"""Vector and semantic job matching using embeddings."""
from __future__ import annotations

import os
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from app.schemas.resume import JobMatchItem, JobMatchOut, ResumeSection

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = os.environ.get("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
        _model = SentenceTransformer(model_name)
    return _model


def _encode(text: str) -> np.ndarray:
    return _get_model().encode(text, convert_to_numpy=True)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def match_jobs(
    resume: ResumeSection,
    jobs: list[dict[str, Any]],
    top_k: int = 10,
    resume_id: Any | None = None,
) -> JobMatchOut:
    """Match resume against job descriptions using embeddings."""
    resume_text = _resume_to_text(resume)
    resume_vec = _encode(resume_text)
    resume_skills = {s.lower() for s in resume.skills}

    matches = []
    for job in jobs:
        job_text = f"{job['title']}. {job.get('description', '')}"
        job_skills = {s.lower() for s in (job.get("required_skills") or [])}
        matched = list(resume_skills & job_skills)
        missing = list(job_skills - resume_skills)

        job_vec = _encode(job_text)
        sim = _cosine(resume_vec, job_vec)

        # Confidence blends semantic similarity and skill overlap
        skill_ratio = len(matched) / max(1, len(job_skills))
        confidence = 0.7 * sim + 0.3 * skill_ratio

        matches.append(
            {
                "job_id": job["id"],
                "title": job["title"],
                "company": job.get("company"),
                "confidence": round(min(1.0, max(0.0, confidence)), 3),
                "missing_skills": missing[:10],
                "matched_skills": matched[:10],
                "reasoning": (
                    f"Semantic similarity {sim:.2f} and {len(matched)}/{len(job_skills)} "
                    f"required skills matched."
                ),
            }
        )

    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return JobMatchOut(
        resume_id=resume_id,
        top_matches=[JobMatchItem(**m) for m in matches[:top_k]],
    )


def _resume_to_text(resume: ResumeSection) -> str:
    parts: list[str] = [
        resume.name or "",
        " ".join(resume.skills),
    ]
    for exp in resume.experience:
        if isinstance(exp, dict):
            parts.append(str(exp.get("title", "")))
            description = exp.get("description", [])
            if isinstance(description, list):
                parts.append(" ".join(str(d) for d in description))
    for edu in resume.education:
        if isinstance(edu, dict):
            parts.append(str(edu.get("degree", "")))
    project_names = [str(p.get("name", "")) for p in resume.projects if isinstance(p, dict)]
    parts.append(" ".join(resume.certifications + project_names + resume.languages + resume.achievements))
    return " ".join([p for p in parts if p])
