from __future__ import annotations

from app.models.schemas import Job
from app.services.llm import DeterministicFallbackProvider
from app.services.scoring import load_profile


def test_deterministic_fallback_analysis():
    job = Job(
        title="RAG & LLM Intern",
        company="AI Labs",
        description="Looking for an intern to build RAG vector search pipelines with FastAPI and Docker.",
        location="Chennai",
    )
    provider = DeterministicFallbackProvider()
    res = provider.analyze_job_description(job)

    assert res.internship is True
    assert "FastAPI" in res.required_skills
    assert "RAG" in res.required_skills
    assert res.confidence == 0.75


def test_deterministic_fallback_questions():
    profile = load_profile()
    provider = DeterministicFallbackProvider()
    answers = provider.generate_application_answers(
        job_title="AI Engineer Intern",
        company="Tech AI",
        jd_text="Build RAG search",
        profile=profile,
        questions=["Why are you a good fit?", "Describe your AI project."]
    )

    assert len(answers) == 2
    assert "RAG" in answers[1].answer
    assert answers[0].requires_user_input is False
