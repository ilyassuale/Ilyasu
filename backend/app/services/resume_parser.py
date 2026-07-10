"""Resume text extraction and structured parsing."""
from __future__ import annotations

import re
from io import BytesIO
from typing import Any

import fitz  # PyMuPDF
from docx import Document

from app.schemas.resume import ResumeSection

SECTION_PATTERNS = {
    "skills": re.compile(r"^(skills|technical skills|core competencies|technologies)\s*[:\-]?(.*)$", re.I),
    "experience": re.compile(r"^(experience|work experience|professional experience|employment)\s*[:\-]?(.*)$", re.I),
    "education": re.compile(r"^(education|academic|qualifications)\s*[:\-]?(.*)$", re.I),
    "certifications": re.compile(r"^(certifications|certificates|licenses)\s*[:\-]?(.*)$", re.I),
    "projects": re.compile(r"^(projects|personal projects|side projects)\s*[:\-]?(.*)$", re.I),
    "languages": re.compile(r"^(languages|language proficiency)\s*[:\-]?(.*)$", re.I),
    "achievements": re.compile(r"^(achievements|awards|honors|accomplishments)\s*[:\-]?(.*)$", re.I),
}


def extract_text(file_bytes: bytes, mime_type: str) -> str:
    mime = mime_type.lower()
    if mime in ("application/pdf", "pdf"):
        return _extract_pdf(file_bytes)
    if mime in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"):
        return _extract_docx(file_bytes)
    if mime.startswith("text/"):
        return file_bytes.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {mime}")


def _extract_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    parts = []
    for page in doc:
        parts.append(page.get_text())
    return "\n".join(parts)


def _extract_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    return "\n".join([p.text for p in document.paragraphs])


def parse_resume(text: str) -> ResumeSection:
    """Rule-based structured extraction from resume text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections = _split_sections(lines)

    name = _extract_name(text)
    skills = _extract_skills(sections.get("skills", []))
    experience = _extract_experience(sections.get("experience", []))
    education = _extract_education(sections.get("education", []))
    certifications = _extract_bullet_list(sections.get("certifications", []))
    projects = _extract_projects(sections.get("projects", []))
    languages = _extract_bullet_list(sections.get("languages", []))
    achievements = _extract_bullet_list(sections.get("achievements", []))

    return ResumeSection(
        name=name,
        skills=skills,
        experience=experience,
        education=education,
        certifications=certifications,
        projects=projects,
        languages=languages,
        achievements=achievements,
    )


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines:
        matched = False
        for section, pattern in SECTION_PATTERNS.items():
            m = pattern.match(line)
            if m:
                current = section
                sections[current] = []
                inline = m.group(2).strip()
                if inline:
                    sections[current].append(inline)
                matched = True
                break
        if not matched and current:
            sections[current].append(line)
    return sections


def _extract_name(text: str) -> str | None:
    first_line = text.strip().split("\n", 1)[0]
    if first_line and len(first_line) < 80 and "@" not in first_line:
        return first_line.strip()
    return None


def _extract_skills(skill_lines: list[str]) -> list[str]:
    combined = " ".join(skill_lines)
    tokens = re.split(r"[,|;\n]", combined)
    skills = [t.strip() for t in tokens if t.strip() and len(t.strip()) < 40]
    return skills


def _extract_experience(lines: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in lines:
        if re.search(r"\d{4}", line) and ("present" in line.lower() or "-" in line):
            if current:
                items.append(current)
            current = {"title": line, "description": []}
        elif current:
            current["description"].append(line)
    if current:
        items.append(current)
    return items


def _extract_education(lines: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in lines:
        if re.search(r"(B\.?S\.?|M\.?S\.?|Ph\.?D\.?|Bachelor|Master|MBA|B\.?Tech|M\.?Tech|Degree)", line, re.I):
            if current:
                items.append(current)
            current = {"degree": line, "description": []}
        elif current:
            current["description"].append(line)
    if current:
        items.append(current)
    return items


def _extract_projects(lines: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in lines:
        if re.search(r"(project|app|platform|system|tool)", line, re.I) and (line[0].isupper() or line.startswith("-")):
            if current:
                items.append(current)
            current = {"name": line.lstrip("- ").strip(), "description": []}
        elif current:
            current["description"].append(line)
    if current:
        items.append(current)
    return items


def _extract_bullet_list(lines: list[str]) -> list[str]:
    result = []
    for line in lines:
        for token in re.split(r"[,|;\n]", line):
            token = token.strip().lstrip("-•* ").strip()
            if token:
                result.append(token)
    return result
