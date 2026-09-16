from __future__ import annotations

import json
import re
from pathlib import Path

from app.services.scoring import PROFILE_PATH

DATA_DIR = PROFILE_PATH.parents[1] / "data"
RESUME_TEXT_PATH = DATA_DIR / "candidate_resume.txt"

SKILL_ALIASES = {
    "python": "Python", "fastapi": "FastAPI", "flask": "Flask", "java": "Java",
    "sql": "SQL", "postgresql": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB",
    "rag": "RAG", "pgvector": "pgvector", "llm": "LLMs", "openai": "OpenAI API",
    "gemini": "Gemini", "claude": "Claude", "ai agent": "AI Agents", "tool calling": "Tool Calling",
    "embeddings": "Embeddings", "semantic search": "Semantic Search", "prompt engineering": "Prompt Engineering",
    "machine learning": "Machine Learning", "deep learning": "Deep Learning", "tensorflow": "TensorFlow",
    "pytorch": "PyTorch", "opencv": "OpenCV", "tesseract": "Tesseract", "docker": "Docker",
    "github actions": "GitHub Actions", "pytest": "Pytest", "react": "React", "typescript": "TypeScript",
    "javascript": "JavaScript", "n8n": "n8n", "rest api": "REST APIs", "rest apis": "REST APIs",
}


def _extract_pdf(raw: bytes) -> str:
    from pypdf import PdfReader
    import io
    reader = PdfReader(io.BytesIO(raw))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(raw: bytes) -> str:
    from docx import Document
    import io
    doc = Document(io.BytesIO(raw))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_resume_text(filename: str, raw: bytes) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".pdf":
        text = _extract_pdf(raw)
    elif suffix == ".docx":
        text = _extract_docx(raw)
    elif suffix in {".txt", ".md"}:
        text = raw.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Upload a PDF, DOCX, TXT, or MD resume.")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) < 150:
        raise ValueError("The resume text could not be read. Please upload a text-based PDF or DOCX.")
    return text[:60000]


def build_profile_from_resume(text: str, filename: str) -> dict:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    lower = text.lower()
    detected = []
    for needle, label in SKILL_ALIASES.items():
        if needle in lower and label not in detected:
            detected.append(label)
    profile["skills"] = detected or profile.get("skills", [])
    profile["resume_file"] = filename
    profile["resume_loaded"] = True
    profile["resume_text_length"] = len(text)
    PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESUME_TEXT_PATH.write_text(text, encoding="utf-8")
    return profile


def resume_status() -> dict:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    return {
        "loaded": RESUME_TEXT_PATH.exists() and profile.get("resume_loaded", False),
        "filename": profile.get("resume_file", ""),
        "text_length": profile.get("resume_text_length", 0),
        "skills_detected": profile.get("skills", []),
    }
