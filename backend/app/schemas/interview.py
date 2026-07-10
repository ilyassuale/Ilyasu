"""Pydantic schemas for interviews, questions, answers, reports."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    resume_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    title: str | None = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question_categories: list[str] = Field(
        default_factory=lambda: ["hr", "technical", "behavioral", "situational"]
    )


class QuestionOut(BaseModel):
    id: uuid.UUID
    sequence: int
    category: str
    question_type: str
    text: str
    context: dict[str, Any] | None = None
    expected_keywords: list[str] | None = None
    difficulty: str | None = None


class AnswerIn(BaseModel):
    question_id: uuid.UUID
    transcript: str | None = None
    code: str | None = None
    selected_option: str | None = None
    duration_seconds: int | None = None
    audio_base64: str | None = None


class AnswerOut(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    transcript: str | None = None
    code: str | None = None
    selected_option: str | None = None
    evaluation: dict[str, Any] | None = None
    created_at: datetime


class InterviewOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    title: str | None = None
    status: str
    difficulty: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class InterviewStateOut(BaseModel):
    interview: InterviewOut
    current_question: QuestionOut | None = None
    questions: list[QuestionOut]
    answers: list[AnswerOut]


class EvaluationCriteria(BaseModel):
    correctness: int = Field(..., ge=0, le=100)
    communication: int = Field(..., ge=0, le=100)
    confidence: int = Field(..., ge=0, le=100)
    relevance: int = Field(..., ge=0, le=100)
    completeness: int = Field(..., ge=0, le=100)
    technical_accuracy: int = Field(..., ge=0, le=100)
    fluency: int = Field(..., ge=0, le=100)
    vocabulary: int = Field(..., ge=0, le=100)
    professionalism: int = Field(..., ge=0, le=100)
    reasoning: str | None = None
    evidence: list[str] = Field(default_factory=list)
    confidence_level: str | None = None


class BehavioralMetrics(BaseModel):
    eye_contact_score: int | None = Field(None, ge=0, le=100)
    head_pose_score: int | None = Field(None, ge=0, le=100)
    expression_score: int | None = Field(None, ge=0, le=100)
    speaking_speed_wpm: int | None = None
    pause_count: int | None = None
    confidence: int | None = Field(None, ge=0, le=100)
    engagement: int | None = Field(None, ge=0, le=100)


class ReportOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    overall_score: int
    section_scores: dict[str, Any]
    strengths: list[str]
    weaknesses: list[str]
    communication_tips: list[str]
    roadmap: dict[str, Any] | None = None
    recommended_courses: list[Any] | None = None
    reasoning: str | None = None
    confidence_level: str | None = None
    created_at: datetime


class TechnicalQuestionOut(BaseModel):
    id: uuid.UUID
    category: Literal["coding", "sql", "system_design", "mcq"]
    text: str
    starter_code: str | None = None
    options: list[str] | None = None
    test_cases: list[dict[str, Any]] | None = None
