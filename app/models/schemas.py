from __future__ import annotations

from pydantic import BaseModel, Field


class Job(BaseModel):
    title: str
    company: str
    description: str = ""
    location: str = ""
    country: str = "India"
    work_mode: str = "unknown"
    stipend_monthly_inr: int | None = None
    source: str = "unknown"
    application_url: str = ""
    skills: list[str] = Field(default_factory=list)
    perks: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    role_relevance: float
    skill_match: float
    location_match: float
    compensation: float
    work_mode: float
    company_signal: float
    total: float
    reasons: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)


class ScoredJob(BaseModel):
    job: Job
    score: ScoreBreakdown
