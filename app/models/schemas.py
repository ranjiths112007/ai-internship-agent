from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class JobAnalysisResult(BaseModel):
    role_type: str = "AI/ML Engineer"
    seniority: str = "Internship"
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)
    location_constraints: list[str] = Field(default_factory=list)
    remote_constraints: list[str] = Field(default_factory=list)
    stipend: dict[str, Any] = Field(default_factory=dict)
    visa_requirement: dict[str, Any] = Field(default_factory=dict)
    international_remote: bool = False
    internship: bool = True
    conversion_signal: dict[str, Any] = Field(default_factory=dict)
    red_flags: list[str] = Field(default_factory=list)
    summary: str = ""
    confidence: float = 0.85


class Job(BaseModel):
    id: Optional[str] = None
    external_id: str = ""
    title: str
    normalized_title: str = ""
    company: str
    description: str = ""
    location: str = ""
    country: str = "India"
    work_mode: str = "unknown"
    remote_category: str = "unknown"
    location_category: str = "unknown"
    employment_type: str = "internship"
    stipend_monthly_inr: Optional[int] = None
    salary_text: str = ""
    currency: str = "INR"
    source: str = "unknown"
    application_url: str = ""
    source_url: str = ""
    skills: list[str] = Field(default_factory=list)
    perks: list[str] = Field(default_factory=list)
    posted_date: str = ""
    deadline: str = ""
    dedup_hash: str = ""
    llm_analysis: Optional[JobAnalysisResult] = None


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


class DiscoveryRunResult(BaseModel):
    sources_checked: int = 0
    jobs_seen: int = 0
    new_jobs: int = 0
    duplicates: int = 0
    failed_sources: int = 0
    high_fit_jobs: int = 0


class QuestionAnswer(BaseModel):
    question: str
    answer: str
    rationale: str = ""
    requires_user_input: bool = False


class QuestionGenerationRequest(BaseModel):
    job_id: Optional[str] = None
    job_title: str = ""
    company: str = ""
    job_description: str = ""
    questions: list[str] = Field(default_factory=list)


class QuestionGenerationResponse(BaseModel):
    job_title: str
    company: str
    answers: list[QuestionAnswer] = Field(default_factory=list)


class ApplicationCreate(BaseModel):
    job_id: str
    status: str = "saved"
    notes: str = ""
    questions_answers: list[QuestionAnswer] = Field(default_factory=list)
    application_url: str = ""
    follow_up_date: str = ""
    recruiter_contact: str = ""


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    questions_answers: Optional[list[QuestionAnswer]] = None
    follow_up_date: Optional[str] = None
    recruiter_contact: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    job: Optional[Job] = None
    status: str
    notes: str
    questions_answers: list[QuestionAnswer] = Field(default_factory=list)
    application_url: str
    applied_at: Optional[str] = None
    follow_up_date: str
    recruiter_contact: str
    source: str
    created_at: str
    updated_at: str


class BrowserPrepareRequest(BaseModel):
    application_id: Optional[str] = None
    job_url: str = ""
    auto_fill: bool = True


class BrowserPrepareResponse(BaseModel):
    status: str  # PREPARED, MANUAL_ACTION_REQUIRED, FAILED
    message: str
    detected_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    screenshot_url: Optional[str] = None
    requires_confirmation: bool = True


class BrowserSubmitRequest(BaseModel):
    application_id: str
    confirmed: bool = False
