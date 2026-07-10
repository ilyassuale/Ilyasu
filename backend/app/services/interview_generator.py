"""Generate adaptive interview questions from resume and job."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.agents.llm_client import chat
from app.schemas.interview import QuestionOut
from app.schemas.resume import JobMatchItem, ResumeSection

CATEGORY_PROMPTS = {
    "hr": "Ask one HR screening question suitable for a {difficulty} interview.",
    "technical": "Ask one technical question based on the candidate's skills and the target role.",  # noqa: E501
    "behavioral": "Ask one behavioral question using the STAR method context.",
    "situational": "Ask one situational question relevant to the target role.",
    "leadership": "Ask one leadership question.",
    "problem_solving": "Ask one problem-solving / critical thinking question.",
    "coding": "Generate one coding problem with starter code in Python. Include test cases.",
    "sql": "Generate one SQL challenge with expected output schema.",
    "system_design": "Generate one system design question for the target role.",
}


SYSTEM_PROMPT = (
    "You are an expert technical interviewer. Generate a single interview question as JSON with the fields:\n"  # noqa: E501
    '- "text": the question text\n'
    '- "question_type": "open" | "mcq" | "coding" | "sql"\n'
    '- "difficulty": "easy" | "medium" | "hard"\n'
    '- "expected_keywords": list of strings\n'
    '- "context": optional dict with hints, test cases, or options\n'
    "Respond with valid JSON only."
)


async def generate_question(
    category: str,
    resume: ResumeSection,
    job: JobMatchItem | None,
    difficulty: str,
    previous_qas: list[dict[str, Any]],
) -> dict[str, Any]:
    base = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["hr"])
    job_title = job.title if job else "Software Engineer"
    job_desc = job.reasoning if job else ""

    previous = "\n".join(
        f"Q: {qa['question']}\nA: {qa['answer']}" for qa in previous_qas[-3:]
    )

    user_prompt = f"""Target role: {job_title}
Job context: {job_desc}
Candidate skills: {', '.join(resume.skills)}
Experience: {len(resume.experience)} roles
Education: {len(resume.education)} entries
Difficulty: {difficulty}
Category: {category}
{base}

Previous Q&A:
{previous}

Generate the next question."""

    result = await asyncio.to_thread(chat, SYSTEM_PROMPT, user_prompt, temperature=0.3, parse_json_output=True)
    if not isinstance(result, dict):
        result = {
            "text": str(result),
            "question_type": "open",
            "difficulty": difficulty,
            "expected_keywords": [],
        }
    return result


async def build_questions(
    categories: list[str],
    resume: ResumeSection,
    job: JobMatchItem | None,
    difficulty: str,
    session_id: uuid.UUID,
    start_sequence: int = 1,
) -> list[QuestionOut]:
    questions: list[QuestionOut] = []
    qas: list[dict[str, Any]] = []
    for i, category in enumerate(categories):
        data = await generate_question(category, resume, job, difficulty, qas)
        q = QuestionOut(
            id=uuid.uuid4(),
            sequence=start_sequence + i,
            category=category,
            question_type=data.get("question_type", "open"),
            text=data.get("text", "Tell me about yourself."),
            context=data.get("context"),
            expected_keywords=data.get("expected_keywords", []),
            difficulty=data.get("difficulty", difficulty),
        )
        questions.append(q)
        qas.append({"question": q.text, "answer": ""})
    return questions
