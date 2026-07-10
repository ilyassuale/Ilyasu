"""SQLAlchemy ORM models."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(50), default="candidate")
    auth_provider: Mapped[str] = mapped_column(String(50), default="email")
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="user", uselist=False)
    resumes: Mapped[list[Resume]] = relationship("Resume", back_populates="user")
    sessions: Mapped[list[InterviewSession]] = relationship("InterviewSession", back_populates="user")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    portfolio_url: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    user: Mapped[User] = relationship("User", back_populates="profile")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
    )


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True)
    logo_url: Mapped[str | None] = mapped_column(String(500))

    jobs: Mapped[list[Job]] = relationship("Job", back_populates="company")
    recruiters: Mapped[list[Recruiter]] = relationship("Recruiter", back_populates="company")


class Recruiter(Base, TimestampMixin):
    __tablename__ = "recruiters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
    )
    internal_role: Mapped[str | None] = mapped_column(String(100))

    user: Mapped[User] = relationship("User")
    company: Mapped[Company] = relationship("Company", back_populates="recruiters")


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    parsed_text: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ats_score: Mapped[int | None] = mapped_column(SmallInteger)
    resume_score: Mapped[int | None] = mapped_column(SmallInteger)
    job_fit_score: Mapped[int | None] = mapped_column(SmallInteger)
    missing_skills: Mapped[list[Any] | None] = mapped_column(JSONB)
    grammar_issues: Mapped[list[Any] | None] = mapped_column(JSONB)
    recommended_roles: Mapped[list[Any] | None] = mapped_column(JSONB)
    strengths: Mapped[list[Any] | None] = mapped_column(JSONB)
    weaknesses: Mapped[list[Any] | None] = mapped_column(JSONB)

    user: Mapped[User] = relationship("User", back_populates="resumes")


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    preferred_skills: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    experience_min: Mapped[int | None] = mapped_column(SmallInteger)
    experience_max: Mapped[int | None] = mapped_column(SmallInteger)
    location: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(50))
    vector_id: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped[Company] = relationship("Company", back_populates="jobs")
    sessions: Mapped[list[InterviewSession]] = relationship("InterviewSession", back_populates="job")


class InterviewSession(Base, TimestampMixin):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id"),
        nullable=True,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id"),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    difficulty: Mapped[str] = mapped_column(String(50), default="medium")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    user: Mapped[User] = relationship("User", back_populates="sessions")
    job: Mapped[Job] = relationship("Job", back_populates="sessions")
    questions: Mapped[list[Question]] = relationship("Question", back_populates="session")
    answers: Mapped[list[Answer]] = relationship("Answer", back_populates="session")
    reports: Mapped[list[Report]] = relationship("Report", back_populates="session")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), default="open")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    expected_keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    difficulty: Mapped[str | None] = mapped_column(String(50))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
    )

    session: Mapped[InterviewSession] = relationship("InterviewSession", back_populates="questions")


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"))
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"))
    transcript: Mapped[str | None] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(String(500))
    code: Mapped[str | None] = mapped_column(Text)
    selected_option: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    word_count: Mapped[int | None] = mapped_column(SmallInteger)
    wpm: Mapped[int | None] = mapped_column(SmallInteger)
    evaluation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
    )

    session: Mapped[InterviewSession] = relationship("InterviewSession", back_populates="answers")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    overall_score: Mapped[int | None] = mapped_column(SmallInteger)
    correctness: Mapped[int | None] = mapped_column(SmallInteger)
    communication: Mapped[int | None] = mapped_column(SmallInteger)
    confidence: Mapped[int | None] = mapped_column(SmallInteger)
    relevance: Mapped[int | None] = mapped_column(SmallInteger)
    completeness: Mapped[int | None] = mapped_column(SmallInteger)
    technical_accuracy: Mapped[int | None] = mapped_column(SmallInteger)
    fluency: Mapped[int | None] = mapped_column(SmallInteger)
    vocabulary: Mapped[int | None] = mapped_column(SmallInteger)
    professionalism: Mapped[int | None] = mapped_column(SmallInteger)
    behavioral_score: Mapped[int | None] = mapped_column(SmallInteger)
    technical_score: Mapped[int | None] = mapped_column(SmallInteger)
    section_scores: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    strengths: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    weaknesses: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    communication_tips: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    roadmap: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    recommended_courses: Mapped[list[Any] | None] = mapped_column(JSONB)
    reasoning: Mapped[str | None] = mapped_column(Text)
    confidence_level: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
    )

    session: Mapped[InterviewSession] = relationship("InterviewSession", back_populates="reports")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
    )
