"""Service unit tests."""
from __future__ import annotations

import base64
import io
import uuid
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.schemas.interview import EvaluationCriteria
from app.schemas.resume import ResumeSection
from app.services.behavioral_analytics import analyze_video_clip, analyze_video_frame
from app.services.evaluator import compute_speech_metrics, evaluate_answer
from app.services.feedback_generator import generate_feedback
from app.services.interview_generator import build_questions, generate_question
from app.services.job_matcher import match_jobs
from app.services.resume_intelligence import analyze_resume
from app.services.resume_parser import extract_text, parse_resume
from app.services.storage import get_file_url, upload_file
from app.services.voice_service import transcribe_audio


def test_parse_resume():
    text = """John Doe
Skills: Python, React, SQL
Experience: Software Engineer at Acme, 2020-2023
Education: B.S. Computer Science
Projects: Interview AI platform
Languages: English, Spanish
"""
    parsed = parse_resume(text)
    assert parsed.name == "John Doe"
    assert "Python" in parsed.skills
    assert len(parsed.experience) > 0


def test_resume_intelligence():
    text = "Python, React, SQL, Docker, AWS."
    resume = ResumeSection(name="Jane", skills=["Python", "React"], experience=[], education=[])
    intel = analyze_resume(resume, text)
    assert 0 <= intel.ats_score <= 100
    assert 0 <= intel.resume_score <= 100
    assert intel.reasoning


def test_job_matcher(monkeypatch):
    import numpy as np

    resume = ResumeSection(
        name="Jane",
        skills=["Python", "Django", "React"],
        experience=[],
        education=[],
    )
    jobs = [
        {
            "id": uuid.uuid4(),
            "title": "Python Backend",
            "description": "Python, Django, PostgreSQL",
            "required_skills": ["python", "django"],
            "company": "A",
        },
        {
            "id": uuid.uuid4(),
            "title": "Frontend",
            "description": "React, CSS",
            "required_skills": ["react", "css"],
            "company": "B",
        },
    ]

    # Mock embeddings to avoid downloading real model weights in CI.
    def _fake_encode(text: str) -> np.ndarray:
        if "Python Backend" in text or "Python" in text:
            return np.array([1.0, 0.0, 0.0, 0.0])
        return np.array([0.0, 1.0, 0.0, 0.0])

    monkeypatch.setattr("app.services.job_matcher._encode", _fake_encode)

    result = match_jobs(resume, jobs, top_k=2, resume_id=uuid.uuid4())
    assert len(result.top_matches) == 2
    assert result.top_matches[0].title == "Python Backend"


def test_feedback_generator():
    evals = [
        EvaluationCriteria(
            correctness=80,
            communication=70,
            confidence=60,
            relevance=90,
            completeness=75,
            technical_accuracy=80,
            fluency=70,
            vocabulary=65,
            professionalism=85,
        )
    ]
    feedback = generate_feedback(evals, ["technical"])
    assert feedback["overall_score"] > 0
    assert feedback["strengths"]


@pytest.mark.asyncio
async def test_evaluate_answer(monkeypatch):
    """Mock LLM and verify scoring."""

    def _fake_chat(*_args, **_kwargs):
        return {
            "correctness": 85,
            "communication": 80,
            "confidence": 75,
            "relevance": 90,
            "completeness": 70,
            "technical_accuracy": 88,
            "fluency": 82,
            "vocabulary": 78,
            "professionalism": 80,
            "reasoning": "Good answer",
            "evidence": ["Used keywords"],
            "confidence_level": "high",
        }

    monkeypatch.setattr("app.services.evaluator.chat", _fake_chat)

    result = await evaluate_answer("What is Python?", "Python is a programming language.", ["python"])
    assert result.correctness == 85
    assert result.relevance == 90
    assert result.reasoning == "Good answer"


@pytest.mark.asyncio
async def test_evaluate_answer_empty():
    result = await evaluate_answer("What is Python?", "")
    assert result.correctness == 0
    assert result.reasoning == "No answer provided."


def test_compute_speech_metrics():
    metrics = compute_speech_metrics("hello world python test code", duration_seconds=5)
    assert metrics["word_count"] == 5
    assert metrics["wpm"] == 60
    assert metrics["pause_count"] >= 0


@pytest.mark.asyncio
async def test_generate_question(monkeypatch):
    """Mock LLM and verify question generation."""

    def _fake_chat(*_args, **_kwargs):
        return {
            "text": "Explain OOP.",
            "question_type": "open",
            "difficulty": "medium",
            "expected_keywords": ["class", "object"],
        }

    monkeypatch.setattr("app.services.interview_generator.chat", _fake_chat)

    resume = ResumeSection(name="A", skills=["Python"], experience=[], education=[])
    result = await generate_question("technical", resume, None, "medium", [])
    assert result["text"] == "Explain OOP."
    assert result["difficulty"] == "medium"


@pytest.mark.asyncio
async def test_build_questions(monkeypatch):
    def _fake_chat(*_args, **_kwargs):
        return {
            "text": "Question",
            "question_type": "open",
            "difficulty": "easy",
            "expected_keywords": [],
        }

    monkeypatch.setattr("app.services.interview_generator.chat", _fake_chat)

    resume = ResumeSection(name="B", skills=["Java"], experience=[], education=[])
    questions = await build_questions(["hr", "technical"], resume, None, "easy", uuid.uuid4())
    assert len(questions) == 2
    assert questions[0].sequence == 1


def test_transcribe_audio(monkeypatch):
    """Mock whisper model and verify transcription."""
    fake_model = MagicMock()
    fake_model.transcribe.return_value = {
        "text": "hello world",
        "language": "en",
        "segments": [],
    }
    monkeypatch.setattr("app.services.voice_service._model", fake_model)

    result = transcribe_audio(b"fake audio bytes")
    assert result["text"] == "hello world"
    assert result["language"] == "en"


def test_upload_file_minio(monkeypatch, tmp_path):
    """Mock Minio path and verify key returned."""
    from app.services import storage

    monkeypatch.setattr(storage.settings, "use_minio", True)
    monkeypatch.setattr(storage.settings, "s3_bucket", "test-bucket")

    fake_client = MagicMock()
    fake_client.bucket_exists.return_value = True
    monkeypatch.setattr(storage, "_get_minio_client", lambda: fake_client)

    key = upload_file(b"resume", "resume.pdf", "application/pdf")
    assert key.startswith("resumes/")
    fake_client.put_object.assert_called_once()


def test_upload_file_minio_creates_bucket(monkeypatch, tmp_path):
    """When bucket is missing, upload_file should create it."""
    from app.services import storage

    monkeypatch.setattr(storage.settings, "use_minio", True)
    monkeypatch.setattr(storage.settings, "s3_bucket", "test-bucket")

    fake_client = MagicMock()
    fake_client.bucket_exists.return_value = False
    monkeypatch.setattr(storage, "_get_minio_client", lambda: fake_client)

    key = upload_file(b"resume", "resume.pdf", "application/pdf")
    assert key.startswith("resumes/")
    fake_client.make_bucket.assert_called_once_with("test-bucket")
    fake_client.put_object.assert_called_once()


def test_upload_file_minio_error_propagated(monkeypatch, tmp_path):
    """put_object errors should propagate."""
    from app.services import storage

    monkeypatch.setattr(storage.settings, "use_minio", True)
    monkeypatch.setattr(storage.settings, "s3_bucket", "test-bucket")

    fake_client = MagicMock()
    fake_client.bucket_exists.return_value = True
    fake_client.put_object.side_effect = RuntimeError("storage down")
    monkeypatch.setattr(storage, "_get_minio_client", lambda: fake_client)

    with pytest.raises(RuntimeError):
        upload_file(b"resume", "resume.pdf", "application/pdf")


def test_upload_file_s3(monkeypatch, tmp_path):
    """Mock S3 path and verify key returned."""
    from app.services import storage

    monkeypatch.setattr(storage.settings, "use_minio", False)
    monkeypatch.setattr(storage.settings, "s3_bucket", "test-bucket")

    fake_client = MagicMock()
    monkeypatch.setattr(storage, "_get_s3_client", lambda: fake_client)

    key = upload_file(b"resume", "resume.pdf", "application/pdf")
    assert key.startswith("resumes/")
    fake_client.put_object.assert_called_once()


def test_get_file_url_minio(monkeypatch):
    from app.services import storage

    monkeypatch.setattr(storage.settings, "use_minio", True)
    monkeypatch.setattr(storage.settings, "s3_endpoint", "http://localhost:9000")
    monkeypatch.setattr(storage.settings, "s3_bucket", "test-bucket")

    url = get_file_url("resumes/abc.pdf")
    assert "localhost" in url


def test_get_file_url_s3(monkeypatch):
    from app.services import storage

    monkeypatch.setattr(storage.settings, "use_minio", False)
    monkeypatch.setattr(storage.settings, "s3_region", "us-east-1")
    monkeypatch.setattr(storage.settings, "s3_bucket", "test-bucket")

    url = get_file_url("resumes/abc.pdf")
    assert "amazonaws.com" in url


def _make_base64_frame() -> str:
    """Create a small 10x10 black PNG frame as a base64 data URI."""
    import cv2

    arr = np.zeros((10, 10, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".png", arr)
    b64 = base64.b64encode(buf).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def test_analyze_video_frame_no_face():
    frame_b64 = _make_base64_frame()
    result = analyze_video_frame(frame_b64)
    assert "error" not in result or result.get("error") == "No faces detected"
    assert "face_detected" in result
    assert not result["face_detected"]


def test_analyze_video_frame_with_face(monkeypatch):
    """Mock face detection to exercise the scoring path."""
    frame_b64 = _make_base64_frame()
    monkeypatch.setattr(
        "app.services.behavioral_analytics._detect_faces",
        lambda _gray: [(2, 2, 6, 6)],
    )
    result = analyze_video_frame(frame_b64)
    assert result["face_detected"] is True
    assert result["confidence"] is not None
    assert 0 <= result["confidence"] <= 100


def test_analyze_video_clip():
    frame_b64 = _make_base64_frame()
    result = analyze_video_clip([frame_b64, frame_b64])
    assert "error" in result or "frames_analyzed" in result


def test_analyze_video_frame_invalid_base64():
    result = analyze_video_frame("not-valid-base64")
    assert "error" in result


def test_extract_text_pdf():
    """Create a minimal PDF and verify text extraction."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Python Developer")
    pdf_bytes = doc.tobytes()
    doc.close()

    text = extract_text(pdf_bytes, "application/pdf")
    assert "Python Developer" in text


def test_extract_text_docx():
    """Create a minimal DOCX and verify text extraction."""
    from docx import Document

    doc = Document()
    doc.add_paragraph("JavaScript Engineer")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    text = extract_text(buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert "JavaScript Engineer" in text


def test_extract_text_plain():
    text = extract_text(b"Plain text resume", "text/plain")
    assert "Plain text" in text


def test_extract_text_unsupported():
    with pytest.raises(ValueError):
        extract_text(b"data", "application/zip")


def test_feedback_generator_llm(monkeypatch):
    """Mock LLM for high-level feedback."""

    def _fake_chat(*_args, **_kwargs):
        return "Excellent performance. Practice more concise responses."

    monkeypatch.setattr("app.services.feedback_generator.chat", _fake_chat)

    from app.schemas.interview import EvaluationCriteria

    evals = [
        EvaluationCriteria(
            correctness=80,
            communication=70,
            confidence=60,
            relevance=90,
            completeness=75,
            technical_accuracy=80,
            fluency=70,
            vocabulary=65,
            professionalism=85,
        )
    ]
    from app.services.feedback_generator import generate_feedback_llm

    feedback = generate_feedback_llm(evals, ["technical"])
    assert "Excellent performance" in feedback["reasoning"]
