"""Interview session, questions, answers, and report routes."""
from __future__ import annotations

import base64
import binascii
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Answer, InterviewSession, Question, Report, Resume, User
from app.schemas.interview import (
    AnswerIn,
    AnswerOut,
    InterviewCreate,
    InterviewOut,
    InterviewStateOut,
    QuestionOut,
    ReportOut,
)
from app.schemas.resume import JobMatchItem, ResumeSection
from app.services.evaluator import compute_speech_metrics, evaluate_answer
from app.services.feedback_generator import generate_feedback
from app.services.interview_generator import build_questions
from app.services.voice_service import transcribe_audio

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post("/", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
async def create_interview(
    payload: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InterviewSession:
    session = InterviewSession(
        user_id=user.id,
        resume_id=payload.resume_id,
        job_id=payload.job_id,
        title=payload.title or "Mock Interview",
        status="pending",
        difficulty=payload.difficulty,
        config={"categories": payload.question_categories},
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/{session_id}/start")
async def start_interview(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InterviewStateOut:
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "active"
    session.started_at = datetime.now(UTC)

    categories = (session.config or {}).get("categories", ["hr", "technical", "behavioral"])
    resume = None
    if session.resume_id:
        r = await db.execute(select(Resume).where(Resume.id == session.resume_id))
        resume_obj = r.scalar_one_or_none()
        if resume_obj and resume_obj.parsed_json:
            resume = ResumeSection(**resume_obj.parsed_json)

    job = None
    if session.job_id:
        # Simplified job context
        job = JobMatchItem(
            job_id=session.job_id,
            title=session.title or "",
            confidence=1.0,
            matched_skills=[],
            missing_skills=[],
            reasoning="",
        )

    questions = await build_questions(
        categories=categories,
        resume=resume or ResumeSection(),
        job=job,
        difficulty=session.difficulty,
        session_id=session.id,
    )

    for q in questions:
        db.add(
            Question(
                session_id=session.id,
                category=q.category,
                question_type=q.question_type,
                text=q.text,
                context=q.context,
                expected_keywords=q.expected_keywords or [],
                difficulty=q.difficulty,
                sequence=q.sequence,
            )
        )

    await db.commit()
    await db.refresh(session)

    q_out = list(questions)
    return InterviewStateOut(
        interview=InterviewOut.model_validate(session),
        current_question=q_out[0] if q_out else None,
        questions=q_out,
        answers=[],
    )


@router.get("/{session_id}", response_model=InterviewStateOut)
async def get_interview_state(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InterviewStateOut:
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = session.questions
    answers = session.answers
    current = next(
        (q for q in questions if q.id not in {a.question_id for a in answers}),
        questions[-1] if questions else None,
    )

    return InterviewStateOut(
        interview=InterviewOut.model_validate(session),
        current_question=QuestionOut.model_validate(current) if current else None,
        questions=[QuestionOut.model_validate(q) for q in questions],
        answers=[AnswerOut.model_validate(a) for a in answers],
    )


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: UUID,
    payload: AnswerIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnswerOut:
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    q_result = await db.execute(
        select(Question).where(Question.id == payload.question_id, Question.session_id == session.id)
    )
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    transcript = payload.transcript or ""
    audio_url = None
    if payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
            whisper_result = transcribe_audio(audio_bytes)
            transcript = whisper_result.get("text", transcript)
            audio_url = "uploaded"
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audio data; unable to decode base64 payload",
            ) from exc
        except Exception as exc:
            logging.exception("Failed to decode/transcribe interview audio")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process audio for transcription",
            ) from exc

    duration = payload.duration_seconds
    metrics = compute_speech_metrics(transcript, duration)
    evaluation = await evaluate_answer(question.text, transcript, question.expected_keywords or [])

    answer = Answer(
        question_id=question.id,
        session_id=session.id,
        transcript=transcript,
        audio_url=audio_url,
        code=payload.code,
        selected_option=payload.selected_option,
        word_count=metrics.get("word_count"),
        wpm=metrics.get("wpm"),
        evaluation=evaluation.model_dump(),
    )
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return AnswerOut.model_validate(answer)


@router.post("/{session_id}/complete", response_model=ReportOut)
async def complete_interview(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportOut:
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    session.completed_at = datetime.now(UTC)

    answers = session.answers
    questions = session.questions
    categories = [q.category for q in questions if q.id in {a.question_id for a in answers}]
    evaluations = [AnswerOut.model_validate(a).evaluation for a in answers if a.evaluation]

    from app.schemas.interview import EvaluationCriteria
    criteria_list = [EvaluationCriteria(**e) for e in evaluations if e]

    feedback = generate_feedback(criteria_list, categories)

    report = Report(
        session_id=session.id,
        user_id=user.id,
        overall_score=feedback["overall_score"],
        section_scores=feedback["section_scores"],
        strengths=feedback["strengths"],
        weaknesses=feedback["weaknesses"],
        communication_tips=feedback["communication_tips"],
        roadmap=feedback["roadmap"],
        recommended_courses=feedback["recommended_courses"],
        reasoning=feedback["reasoning"],
        confidence_level=feedback["confidence_level"],
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return ReportOut.model_validate(report)


@router.get("/{session_id}/report", response_model=ReportOut)
async def get_report(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportOut:
    result = await db.execute(
        select(Report).where(Report.session_id == session_id, Report.user_id == user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportOut.model_validate(report)
