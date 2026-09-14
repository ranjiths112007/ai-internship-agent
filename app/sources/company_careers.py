from __future__ import annotations

import logging
from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)


class CuratedCompanyCareersSource(JobSource):
    """
    Curated company career source providing high-quality sample AI internship opportunities
    representing top AI startups and tech firms in India and worldwide remote.
    """

    def __init__(self, name: str = "Curated AI Careers"):
        self.name = name

    def fetch_jobs(self) -> list[Job]:
        return [
            Job(
                external_id="curated-001",
                title="Generative AI & LLM Engineer Intern",
                company="HyperScale AI Labs",
                description="Looking for an AI Engineer Intern to work on RAG pipelines, pgvector semantic search, Google Gemini, and OpenAI API integrations. Build real-time AI agents with tool calling and FastAPI.",
                location="Bengaluru",
                country="India",
                work_mode="remote",
                stipend_monthly_inr=50000,
                source=self.name,
                application_url="https://hyperscale.ai/careers/genai-intern",
                skills=["Python", "FastAPI", "RAG", "LLMs", "pgvector", "AI Agents", "Google Gemini", "Docker"],
                perks=["lunch", "mentor", "conversion", "snacks"],
            ),
            Job(
                external_id="curated-002",
                title="AI Agent & Systems Intern",
                company="Nexus AI Corp",
                description="Build production tool-using AI agents, OAuth 2.0 API integrations, custom prompt engineering pipelines, and structured output parsers.",
                location="Chennai",
                country="India",
                work_mode="onsite",
                stipend_monthly_inr=45000,
                source=self.name,
                application_url="https://nexusai.tech/jobs/agent-intern",
                skills=["Python", "FastAPI", "AI Agents", "Tool Calling", "REST APIs", "SQLAlchemy", "PostgreSQL"],
                perks=["breakfast", "lunch", "snacks", "learning"],
            ),
            Job(
                external_id="curated-003",
                title="Applied ML & Computer Vision Intern",
                company="VisionMetrics",
                description="Develop document intelligence pipelines using OpenCV, Tesseract OCR, PyTorch, and FastAPI. Build end-to-end invoice and text parsing services.",
                location="Coimbatore",
                country="India",
                work_mode="hybrid",
                stipend_monthly_inr=42000,
                source=self.name,
                application_url="https://visionmetrics.io/careers/cv-intern",
                skills=["Python", "OpenCV", "Tesseract OCR", "FastAPI", "Docker", "Pytest"],
                perks=["mentor", "learning", "snacks"],
            ),
            Job(
                external_id="curated-004",
                title="AI Engineer Intern — Global Remote",
                company="Aetheric Systems (US Startup)",
                description="Join an early-stage US AI startup as a Remote AI Engineer Intern. Build sentence-transformers embeddings, pgvector vector search, and tool-calling microservices.",
                location="Remote - Unrestricted",
                country="Worldwide",
                work_mode="remote",
                stipend_monthly_inr=75000,
                source=self.name,
                application_url="https://aetheric.ai/careers/global-ai-intern",
                skills=["Python", "RAG", "LLMs", "Sentence Transformers", "pgvector", "TypeScript", "Next.js"],
                perks=["conversion", "mentor", "learning"],
            ),
            Job(
                external_id="curated-005",
                title="Senior Backend Systems Engineer",
                company="Legacy Enterprise Corp",
                description="Requires 5+ years experience in C++ and distributed databases.",
                location="Bengaluru",
                country="India",
                work_mode="onsite",
                stipend_monthly_inr=150000,
                source=self.name,
                application_url="https://legacycorp.com/careers/sr-backend",
                skills=["C++", "Java", "Distributed Systems"],
                perks=[],
            ),
        ]
