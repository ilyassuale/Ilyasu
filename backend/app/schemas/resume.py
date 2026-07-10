"""Pydantic schemas for resumes and parsing."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeUploadOut(BaseModel):
    id: uuid.UUID
    file_name: str
    status: str = "uploaded"


class ResumeSection(BaseModel):
    name: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ResumeIntelligence(BaseModel):
    resume_score: int = Field(..., ge=0, le=100)
    ats_score: int = Field(..., ge=0, le=100)
    job_fit_score: int | None = Field(None, ge=0, le=100)
    missing_skills: list[str] = Field(default_factory=list)
    grammar_issues: list[str] = Field(default_factory=list)
    recommended_roles: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    reasoning: str | None = None
    confidence_level: str | None = None


class ResumeOut(BaseModel):
    id: uuid.UUID
    file_name: str
    parsed_json: ResumeSection | None = None
    parsed_text: str | None = None
    intelligence: ResumeIntelligence | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeIntelligenceOut(BaseModel):
    resume_id: uuid.UUID
    parsed: ResumeSection
    intelligence: ResumeIntelligence
    processing_time_ms: int


class JobMatchItem(BaseModel):
    job_id: uuid.UUID
    title: str
    company: str | None = None
    confidence: float = Field(..., ge=0, le=1)
    missing_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    reasoning: str | None = None


class JobMatchOut(BaseModel):
    resume_id: uuid.UUID | None
    top_matches: list[JobMatchItem]
