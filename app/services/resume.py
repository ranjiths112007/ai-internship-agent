from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.db.models import CandidateProfileModel
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

PROFILE_PATH = Path(__file__).resolve().parents[2] / "config" / "candidate_profile.json"
DATA_DIR = PROFILE_PATH.parents[1] / "data"
RESUME_TEXT_PATH = DATA_DIR / "candidate_resume.txt"

SKILL_ALIASES = {
    "python": "Python", "fastapi": "FastAPI", "flask": "Flask", "java": "Java", "c++": "C++",
    "sql": "SQL", "postgresql": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB",
    "rag": "RAG", "pgvector": "pgvector", "llm": "LLMs", "openai": "OpenAI API",
    "gemini": "Google Gemini", "claude": "Claude", "ai agent": "AI Agents", "tool calling": "Tool Calling",
    "embeddings": "Embeddings", "semantic search": "Semantic Search", "prompt engineering": "Prompt Engineering",
    "machine learning": "Machine Learning", "deep learning": "Deep Learning", "tensorflow": "TensorFlow",
    "pytorch": "PyTorch", "opencv": "OpenCV", "tesseract": "Tesseract OCR", "docker": "Docker",
    "docker compose": "Docker Compose", "github actions": "GitHub Actions", "pytest": "Pytest",
    "react": "React", "typescript": "TypeScript", "javascript": "JavaScript", "n8n": "n8n",
    "rest api": "REST APIs", "rest apis": "REST APIs", "scikit-learn": "Scikit-learn",
    "pandas": "Pandas", "numpy": "NumPy", "xgboost": "XGBoost", "langchain": "LangChain",
    "llamaIndex": "LlamaIndex", "git": "Git", "linux": "Linux"
}

DEFAULT_TARGET_ROLES = [
    "AI Engineer Intern",
    "Generative AI Intern",
    "Applied AI Intern",
    "Machine Learning Engineer Intern",
    "AI/ML Engineer Intern",
    "LLM Engineer Intern",
    "RAG Engineer Intern",
    "AI Agent Engineer Intern"
]

DEFAULT_LOCATIONS = ["Bengaluru", "Chennai", "Coimbatore"]


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
        raise ValueError("Unsupported format. Please upload a PDF, DOCX, TXT, or MD resume.")

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) < 100:
        raise ValueError("The resume text could not be extracted. Please upload a text-based document.")
    return text[:60000]


def parse_resume_fields(text: str) -> dict[str, Any]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lower_text = text.lower()

    name = lines[0] if lines else "Candidate"
    if "@" in name or len(name) > 60:
        name = "Candidate"

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    email = email_match.group(0) if email_match else ""

    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}", text)
    phone = phone_match.group(0).strip() if phone_match else ""

    location = "India"
    for loc in ["Chennai", "Bengaluru", "Bangalore", "Coimbatore", "Hyderabad", "Mumbai", "Pune", "Delhi"]:
        if loc.lower() in lower_text:
            location = f"{loc}, India"
            break

    degree = "Not detected"
    if "b.sc" in lower_text or "bachelor" in lower_text or "b.tech" in lower_text or "b.e" in lower_text:
        for line in lines[:15]:
            if any(k in line.lower() for k in ["b.sc", "bachelor", "b.tech", "b.e", "degree"]):
                degree = line
                break

    university = "Not detected"
    for line in lines[:20]:
        if any(k in line.lower() for k in ["university", "college", "institute", "academy"]):
            university = line
            break

    year_match = re.search(r"\b(202[3-9]|2030)\b", text)
    grad_year = int(year_match.group(0)) if year_match else 2027

    cgpa_match = re.search(r"\b(cgpa|gpa)[\s:]*([0-9]\.[0-9]{1,2})\b", lower_text)
    cgpa = float(cgpa_match.group(2)) if cgpa_match else None

    detected_skills = []
    for needle, label in SKILL_ALIASES.items():
        if needle in lower_text and label not in detected_skills:
            detected_skills.append(label)

    projects = []
    experience = []
    in_projects = False
    in_exp = False

    for line in lines:
        l_low = line.lower()
        if "project" in l_low and len(line) < 30:
            in_projects = True
            in_exp = False
            continue
        elif any(h in l_low for h in ["experience", "internship", "employment", "work history"]) and len(line) < 30:
            in_exp = True
            in_projects = False
            continue
        elif any(h in l_low for h in ["education", "skills", "certifications"]) and len(line) < 30:
            in_projects = False
            in_exp = False

        if in_projects and len(line) > 10:
            projects.append(line)
        elif in_exp and len(line) > 10:
            experience.append(line)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "degree": degree,
        "university": university,
        "graduation_year": grad_year,
        "cgpa": cgpa,
        "skills": detected_skills,
        "projects": projects[:10],
        "experience": experience[:10],
        "target_roles": DEFAULT_TARGET_ROLES,
        "preferred_locations": DEFAULT_LOCATIONS,
        "preferred_work_modes": ["onsite", "remote"],
        "minimum_stipend_inr": 40000,
        "international_remote": True,
    }


def build_profile_from_resume(text: str, filename: str) -> dict:
    parsed = parse_resume_fields(text)
    parsed["resume_filename"] = filename
    parsed["resume_loaded"] = True
    parsed["resume_text"] = text
    parsed["resume_updated_at"] = datetime.now(timezone.utc).isoformat()

    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESUME_TEXT_PATH.write_text(text, encoding="utf-8")

    save_profile_to_db(parsed)

    return parsed


def save_profile_to_db(profile_data: dict) -> None:
    db = SessionLocal()
    try:
        profile_row = db.query(CandidateProfileModel).filter(CandidateProfileModel.id == "default").first()
        if not profile_row:
            profile_row = CandidateProfileModel(id="default")
            db.add(profile_row)

        profile_row.name = profile_data.get("name", "Candidate")
        profile_row.email = profile_data.get("email", "")
        profile_row.phone = profile_data.get("phone", "")
        profile_row.location = profile_data.get("location", "")
        profile_row.degree = profile_data.get("degree", "")
        profile_row.university = profile_data.get("university", "")
        profile_row.graduation_year = profile_data.get("graduation_year")
        profile_row.cgpa = profile_data.get("cgpa")
        profile_row.skills_json = json.dumps(profile_data.get("skills", []))
        profile_row.projects_json = json.dumps(profile_data.get("projects", []))
        profile_row.experience_json = json.dumps(profile_data.get("experience", []))
        profile_row.target_roles_json = json.dumps(profile_data.get("target_roles", DEFAULT_TARGET_ROLES))
        profile_row.preferred_locations_json = json.dumps(profile_data.get("preferred_locations", DEFAULT_LOCATIONS))
        profile_row.preferred_work_modes_json = json.dumps(profile_data.get("preferred_work_modes", ["onsite", "remote"]))
        profile_row.minimum_stipend_monthly_inr = profile_data.get("minimum_stipend_inr", 40000)
        profile_row.international_remote = 1 if profile_data.get("international_remote", True) else 0
        profile_row.resume_filename = profile_data.get("resume_filename", "")
        profile_row.resume_text = profile_data.get("resume_text", "")

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save profile to SQLite DB: %s", exc)
    finally:
        db.close()


def get_profile_dict() -> dict:
    db = SessionLocal()
    try:
        row = db.query(CandidateProfileModel).filter(CandidateProfileModel.id == "default").first()
        if row and row.skills_json:
            return {
                "candidate": {
                    "name": row.name or "Candidate",
                    "email": row.email or "",
                    "phone": row.phone or "",
                    "education": f"{row.degree or 'Student'} · {row.university or 'University'}",
                    "graduation_year": row.graduation_year or 2027,
                    "cgpa": row.cgpa or 8.0,
                    "current_city": row.location or "Chennai, India",
                },
                "target_roles": json.loads(row.target_roles_json or "[]") or DEFAULT_TARGET_ROLES,
                "locations": json.loads(row.preferred_locations_json or "[]") or DEFAULT_LOCATIONS,
                "work_modes": json.loads(row.preferred_work_modes_json or "[]") or ["onsite", "remote"],
                "international_remote": bool(row.international_remote),
                "minimum_monthly_stipend_inr": row.minimum_stipend_monthly_inr or 40000,
                "skills": json.loads(row.skills_json or "[]"),
                "projects": json.loads(row.projects_json or "[]"),
                "experience": json.loads(row.experience_json or "[]"),
                "resume_file": row.resume_filename or "",
                "resume_loaded": bool(row.resume_filename),
                "resume_text_length": len(row.resume_text or ""),
            }
    except Exception as exc:
        logger.warning("DB profile fetch failed, using json file fallback: %s", exc)
    finally:
        db.close()

    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "candidate": {
            "name": "Candidate Profile",
            "education": "AI & ML",
            "graduation_year": 2027,
            "cgpa": 8.0,
            "current_city": "India"
        },
        "target_roles": DEFAULT_TARGET_ROLES,
        "locations": DEFAULT_LOCATIONS,
        "work_modes": ["onsite", "remote"],
        "international_remote": True,
        "minimum_monthly_stipend_inr": 40000,
        "skills": ["Python", "FastAPI", "Machine Learning", "RAG", "LLMs"],
        "resume_loaded": False
    }


def resume_status() -> dict:
    profile = get_profile_dict()
    return {
        "loaded": profile.get("resume_loaded", False),
        "filename": profile.get("resume_file", ""),
        "text_length": profile.get("resume_text_length", 0),
        "skills_detected": profile.get("skills", []),
    }
