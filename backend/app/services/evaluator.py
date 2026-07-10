"""Evaluate candidate answers with LLM and rule-based metrics."""
from __future__ import annotations

import asyncio
import re
from typing import Any

from app.agents.llm_client import chat
from app.schemas.interview import EvaluationCriteria

SYSTEM_PROMPT = """You are an expert interview evaluator. Evaluate the candidate's answer to the question.
Return a JSON object with integer scores from 0-100 for the following fields:
- correctness
- communication
- confidence
- relevance
- completeness
- technical_accuracy
- fluency
- vocabulary
- professionalism
Also include:
- reasoning (string explaining the evaluation)
- evidence (list of strings from the transcript supporting the score)
- confidence_level ("low" | "medium" | "high")
Respond with valid JSON only."""


async def evaluate_answer(question: str, answer: str, expected_keywords: list[str] | None = None) -> EvaluationCriteria:
    if not answer:
        return EvaluationCriteria(
            correctness=0,
            communication=0,
            confidence=0,
            relevance=0,
            completeness=0,
            technical_accuracy=0,
            fluency=0,
            vocabulary=0,
            professionalism=0,
            reasoning="No answer provided.",
            evidence=[],
            confidence_level="high",
        )

    user_prompt = f"""Question: {question}

Candidate Answer: {answer}

Expected keywords: {', '.join(expected_keywords or [])}

Evaluate the answer."""

    result = await asyncio.to_thread(chat, SYSTEM_PROMPT, user_prompt, temperature=0.2, parse_json_output=True)
    if not isinstance(result, dict):
        result = {}

    def _score(key: str) -> int:
        val = result.get(key)
        if val is None:
            return 50
        try:
            return max(0, min(100, int(val)))
        except (TypeError, ValueError):
            return 50

    # Fallback keyword relevance
    answer_lower = answer.lower()
    keyword_hits = sum(1 for kw in (expected_keywords or []) if kw.lower() in answer_lower)
    relevance = _score("relevance")
    if keyword_hits:
        relevance = min(100, max(relevance, int(50 + 10 * keyword_hits)))

    return EvaluationCriteria(
        correctness=_score("correctness"),
        communication=_score("communication"),
        confidence=_score("confidence"),
        relevance=relevance,
        completeness=_score("completeness"),
        technical_accuracy=_score("technical_accuracy"),
        fluency=_score("fluency"),
        vocabulary=_score("vocabulary"),
        professionalism=_score("professionalism"),
        reasoning=result.get("reasoning", "Evaluation based on content and keyword alignment."),
        evidence=result.get("evidence", []) if isinstance(result.get("evidence"), list) else [],
        confidence_level=result.get("confidence_level", "medium"),
    )


def compute_speech_metrics(transcript: str, duration_seconds: int | None = None) -> dict[str, Any]:
    words = transcript.split()
    word_count = len(words)
    wpm = None
    if duration_seconds and duration_seconds > 0:
        wpm = int((word_count / duration_seconds) * 60)
    pause_count = len(re.findall(r"[.,;!?]", transcript))
    return {
        "word_count": word_count,
        "wpm": wpm,
        "pause_count": pause_count,
    }
