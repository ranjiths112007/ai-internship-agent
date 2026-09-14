from __future__ import annotations

from app.models.schemas import Job
from app.services.normalization import normalize_job
from app.services.scoring import score_job


def test_score_strong_ai_intern():
    job = Job(
        title="Generative AI & LLM Engineer Intern",
        company="HyperScale AI",
        description="Looking for an intern to work on RAG pipelines, pgvector vector search, Gemini, and FastAPI microservices.",
        location="Bengaluru",
        country="India",
        work_mode="remote",
        stipend_monthly_inr=50000,
    )
    norm_job = normalize_job(job)
    breakdown = score_job(norm_job)

    assert breakdown.total >= 75.0
    assert breakdown.role_relevance >= 80.0
    assert breakdown.compensation == 100.0
    assert any("RAG" in r for r in breakdown.reasons)


def test_score_senior_role_penalty():
    job = Job(
        title="Senior AI Engineer",
        company="Enterprise Systems",
        description="Requires 5+ years experience in distributed C++ and PyTorch infrastructure.",
        location="Bengaluru",
        stipend_monthly_inr=150000,
    )
    norm_job = normalize_job(job)
    breakdown = score_job(norm_job)

    assert any("senior-level" in f for f in breakdown.flags)
    assert breakdown.role_relevance < 70.0


def test_score_international_remote_lane():
    job = Job(
        title="AI Engineer Intern — Global Remote",
        company="US Tech Startup",
        description="Remote internship open worldwide for AI engineering candidates.",
        location="Remote - Worldwide",
        country="Worldwide",
        work_mode="remote",
        stipend_monthly_inr=80000,
    )
    norm_job = normalize_job(job)
    breakdown = score_job(norm_job)

    assert breakdown.location_match == 100.0
    assert any("International Remote" in r for r in breakdown.reasons)


def test_score_undisclosed_stipend_flag():
    job = Job(
        title="AI Intern",
        company="Stealth AI",
        description="Exciting AI internship.",
        location="Chennai",
        stipend_monthly_inr=None,
    )
    norm_job = normalize_job(job)
    breakdown = score_job(norm_job)

    assert any("undisclosed" in f.lower() for f in breakdown.flags)
    assert breakdown.compensation == 45.0
