from __future__ import annotations

from app.models.schemas import Job
from app.services.normalization import classify_location_and_remote, extract_skills, normalize_job, normalize_title


def test_title_normalization_is_stable():
    assert normalize_title("  GenAI / LLM Engineer — Intern! ") == "genai llm engineer intern"


def test_location_aliases_and_remote_scope():
    assert classify_location_and_remote("Bangalore, India", "India", "onsite") == ("onsite", "india")
    assert classify_location_and_remote("Remote - India", "India", "remote") == ("india_remote", "india")
    assert classify_location_and_remote("Remote - Worldwide", "Worldwide", "remote") == ("worldwide_remote", "international_remote")
    assert classify_location_and_remote("Remote", "Unknown", "remote") == ("unknown", "unknown")


def test_skill_extraction_is_bounded_and_deterministic():
    text = "Build a RAG service with Python, FastAPI, pgvector, Docker and React."
    skills = extract_skills(text)
    assert "python" in skills
    assert "fastapi" in skills
    assert "rag" in skills
    assert "pgvector" in skills
    assert skills == extract_skills(text)
    assert len(skills) <= 50


def test_normalization_does_not_convert_foreign_currency_to_inr():
    job = Job(
        title="ML Intern",
        company="Global AI",
        description="PyTorch and Python",
        location="Remote - United States",
        country="United States",
        work_mode="remote",
        currency="USD",
        stipend_monthly_inr=5000,
    )
    normalized = normalize_job(job)
    assert normalized.stipend_monthly_inr is None
    assert normalized.currency == "USD"
    assert normalized.location_category == "international_remote"
