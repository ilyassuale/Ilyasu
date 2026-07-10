"""Aggregate interview data into a final report."""
from __future__ import annotations

from statistics import mean
from typing import Any

from app.agents.llm_client import chat
from app.schemas.interview import EvaluationCriteria


def generate_feedback(
    evaluations: list[EvaluationCriteria],
    question_categories: list[str],
) -> dict[str, Any]:
    if not evaluations:
        return {
            "overall_score": 0,
            "section_scores": {},
            "strengths": [],
            "weaknesses": ["No answers submitted."],
            "communication_tips": [],
            "roadmap": {},
            "recommended_courses": [],
            "reasoning": "No evaluation data available.",
            "confidence_level": "high",
        }

    scores = {
        "correctness": int(mean([e.correctness for e in evaluations])),
        "communication": int(mean([e.communication for e in evaluations])),
        "confidence": int(mean([e.confidence for e in evaluations])),
        "relevance": int(mean([e.relevance for e in evaluations])),
        "completeness": int(mean([e.completeness for e in evaluations])),
        "technical_accuracy": int(mean([e.technical_accuracy for e in evaluations])),
        "fluency": int(mean([e.fluency for e in evaluations])),
        "vocabulary": int(mean([e.vocabulary for e in evaluations])),
        "professionalism": int(mean([e.professionalism for e in evaluations])),
    }

    overall = int(mean(scores.values()))

    # Categorize section scores by question category
    section_scores = {}
    if question_categories:
        for category in set(question_categories):
            cat_evals = [e for e, cat in zip(evaluations, question_categories) if cat == category]
            if cat_evals:
                section_scores[category] = int(mean([mean([getattr(e, k) for k in scores]) for e in cat_evals]))

    # Strengths / weaknesses
    strengths = []
    weaknesses = []
    for k, v in scores.items():
        if v >= 80:
            strengths.append(f"Strong {k.replace('_', ' ')}.")
        elif v < 50:
            weaknesses.append(f"Improve {k.replace('_', ' ')}.")

    if not strengths:
        strengths.append("Consistent participation.")
    if not weaknesses:
        weaknesses.append("Continue practicing concise, structured responses.")

    communication_tips = [
        "Use the STAR method for behavioral questions.",
        "Keep answers concise and relevant.",
        "Pause briefly before answering complex questions.",
        "Maintain steady eye contact and speak clearly.",
    ]

    roadmap = {
        "1_week": ["Record practice answers and review filler words.", "Study top missing skills."],
        "1_month": ["Complete 5 mock interviews.", "Build a portfolio project."],
        "3_months": ["Deep dive into system design.", "Contribute to open source."],
    }

    recommended_courses = [
        {"title": "System Design Interview", "provider": "Educative", "url": "https://www.educative.io"},
        {"title": "Python for Data Structures", "provider": "Coursera", "url": "https://www.coursera.org"},
    ]

    return {
        "overall_score": overall,
        "section_scores": section_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "communication_tips": communication_tips,
        "roadmap": roadmap,
        "recommended_courses": recommended_courses,
        "reasoning": (
            f"Overall {overall} based on {len(evaluations)} answers "
            f"across {len(set(question_categories))} categories."
        ),
        "confidence_level": "high",
    }


def generate_feedback_llm(
    evaluations: list[EvaluationCriteria],
    question_categories: list[str],
) -> dict[str, Any]:
    base = generate_feedback(evaluations, question_categories)
    system = (
        "You are a career coach. Summarize interview performance in 2-3 sentences "
        "and provide one actionable improvement."
    )
    user = (
        f"Scores: {base['section_scores']}\n"
        f"Strengths: {base['strengths']}\n"
        f"Weaknesses: {base['weaknesses']}"
    )
    summary = chat(system, user, temperature=0.4)
    base["reasoning"] = f"{base['reasoning']} {summary}"
    return base
