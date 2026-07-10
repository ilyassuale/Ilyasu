"""Resume scoring, ATS, grammar, and recommendations."""
from __future__ import annotations

import re

from app.schemas.resume import ResumeIntelligence, ResumeSection

# Minimal lists for rule-based scoring
TECH_KEYWORDS = {
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "ruby",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring",
    "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "aws",
    "azure", "gcp", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "git", "ci/cd", "github actions", "linux", "terraform", "ansible",
}

SOFT_SKILLS = {
    "communication", "leadership", "teamwork", "problem solving", "critical thinking",
    "adaptability", "creativity", "time management", "collaboration", "mentoring",
}


def analyze_resume(resume: ResumeSection, text: str) -> ResumeIntelligence:
    text_lower = text.lower()

    # ATS score: contact info, sections, keywords density
    ats = _compute_ats_score(resume, text_lower)

    # Resume score: content quality, structure, skill diversity
    resume_score = _compute_resume_score(resume, text_lower)

    # Missing hard skills (relative to a baseline tech set)
    missing = sorted([kw for kw in TECH_KEYWORDS if kw not in text_lower])
    if len(missing) > 10:
        missing = missing[:10]

    # Grammar issues: simple heuristics
    grammar = _grammar_issues(text)

    # Recommended roles
    roles = _recommend_roles(resume, text_lower)

    # Strengths / weaknesses
    strengths, weaknesses = _strengths_weaknesses(resume, text_lower, missing)

    reasoning = (
        f"Resume analysis based on {len(resume.skills)} skills, "
        f"{len(resume.experience)} experience entries, and {len(resume.education)} education entries."
        " ATS score reflects section completeness and keyword density."
    )

    return ResumeIntelligence(
        resume_score=resume_score,
        ats_score=ats,
        job_fit_score=resume_score,
        missing_skills=missing,
        grammar_issues=grammar,
        recommended_roles=roles,
        strengths=strengths,
        weaknesses=weaknesses,
        reasoning=reasoning,
        confidence_level="medium",
    )


def _compute_ats_score(resume: ResumeSection, text: str) -> int:
    score = 0
    if resume.name:
        score += 10
    if "@" in text and re.search(r"\b\d{10}\b|\d{3}-\d{3}-\d{4}", text):
        score += 10
    if resume.education:
        score += 15
    if resume.experience:
        score += 20
    if resume.skills:
        score += 15
    if resume.certifications:
        score += 10
    if resume.projects:
        score += 10
    keyword_hits = sum(1 for kw in TECH_KEYWORDS if kw in text)
    score += min(10, keyword_hits)
    return min(100, score)


def _compute_resume_score(resume: ResumeSection, text: str) -> int:
    score = 40
    score += min(20, len(resume.skills) * 2)
    score += min(20, len(resume.experience) * 5)
    score += min(10, len(resume.projects) * 3)
    soft_hits = sum(1 for kw in SOFT_SKILLS if kw in text)
    score += min(10, soft_hits)
    return min(100, score)


def _grammar_issues(text: str) -> list[str]:
    issues = []
    # Common mistakes
    if re.search(r"\bi\b", text):
        # suggest consistent capitalization
        pass
    if "  " in text:
        issues.append("Multiple consecutive spaces detected.")
    if re.search(r"[.!?]{2,}", text):
        issues.append("Avoid multiple punctuation marks.")
    if len(re.findall(r"\b\w{3,}\b", text)) < 50:
        issues.append("Resume content appears too brief.")
    return issues


def _recommend_roles(resume: ResumeSection, text: str) -> list[str]:
    text_lower = text
    roles = []
    if "python" in text_lower or "django" in text_lower or "flask" in text_lower:
        roles.append("Backend Engineer")
        roles.append("Python Developer")
    if any(k in text_lower for k in ("react", "angular", "vue", "frontend")):
        roles.append("Frontend Engineer")
    if any(k in text_lower for k in ("machine learning", "data", "tensorflow", "pytorch")):
        roles.append("Machine Learning Engineer")
        roles.append("Data Scientist")
    if any(k in text_lower for k in ("docker", "kubernetes", "aws", "terraform")):
        roles.append("DevOps Engineer")
        roles.append("Cloud Engineer")
    if not roles:
        roles.append("Software Engineer")
    return roles[:5]


def _strengths_weaknesses(
    resume: ResumeSection, text: str, missing: list[str]
) -> tuple[list[str], list[str]]:
    strengths = []
    weaknesses = []
    if len(resume.skills) >= 8:
        strengths.append("Broad technical skill set.")
    if len(resume.experience) >= 2:
        strengths.append("Demonstrated professional experience.")
    if resume.projects:
        strengths.append("Hands-on project experience.")
    if len(resume.skills) < 5:
        weaknesses.append("Limited skills section.")
    if not resume.projects:
        weaknesses.append("No projects listed.")
    if missing:
        weaknesses.append(f"Missing in-demand skills: {', '.join(missing[:5])}.")
    if not weaknesses:
        weaknesses.append("Consider adding more quantifiable achievements.")
    return strengths, weaknesses
