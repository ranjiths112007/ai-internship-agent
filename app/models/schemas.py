from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


ApplicationStatus = Literal[
    "saved", "discovered", "shortlisted", "applying", "applied",
    "assessment", "interview", "rejected", "offer", "withdrawn",
]


class JobAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
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
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)


class Job(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: Optional[str] = None
    external_id: str = ""
    title: str = Field(min_length=1, max_length=255)
    normalized_title: str = ""
    company: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=20000)
    location: str = Field(default="", max_length=255)
    country: str = Field(default="India", max_length=100)
    work_mode: str = Field(default="unknown", max_length=50)
    remote_category: str = Field(default="unknown", max_length=50)
    location_category: str = Field(default="unknown", max_length=50)
    employment_type: str = Field(default="internship", max_length=50)
    stipend_monthly_inr: Optional[int] = Field(default=None, ge=0)
    salary_text: str = Field(default="", max_length=500)
    currency: str = Field(default="INR", min_length=3, max_length=10)
    source: str = Field(default="unknown", max_length=100)
    application_url: str = Field(default="", max_length=2000)
    source_url: str = Field(default="", max_length=2000)
    skills: list[str] = Field(default_factory=list, max_length=100)
    perks: list[str] = Field(default_factory=list, max_length=100)
    posted_date: str = ""
    deadline: str = ""
    dedup_hash: str = ""
    llm_analysis: Optional[JobAnalysisResult] = None

    @field_validator("title", "company", "location", "country", mode="before")
    @classmethod
    def clean_text(cls, value: Any) -> Any:
        if value is None:
            return ""
        return " ".join(str(value).split())


class ScoreBreakdown(BaseModel):
    role_relevance: float = Field(ge=0, le=100)
    skill_match: float = Field(ge=0, le=100)
    location_match: float = Field(ge=0, le=100)
    compensation: float = Field(ge=0, le=100)
    work_mode: float = Field(ge=0, le=100)
    company_signal: float = Field(ge=0, le=100)
    total: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list, max_length=30)
    flags: list[str] = Field(default_factory=list, max_length=30)


class ScoredJob(BaseModel):
    job: Job
    score: ScoreBreakdown


class DiscoveryRunResult(BaseModel):
    sources_checked: int = Field(default=0, ge=0)
    jobs_seen: int = Field(default=0, ge=0)
    new_jobs: int = Field(default=0, ge=0)
    duplicates: int = Field(default=0, ge=0)
    failed_sources: int = Field(default=0, ge=0)
    high_fit_jobs: int = Field(default=0, ge=0)


class QuestionAnswer(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(default="", max_length=10000)
    rationale: str = Field(default="", max_length=3000)
    requires_user_input: bool = False


class QuestionGenerationRequest(BaseModel):
    job_id: Optional[str] = None
    job_title: str = Field(default="", max_length=255)
    company: str = Field(default="", max_length=255)
    job_description: str = Field(default="", max_length=20000)
    questions: list[str] = Field(default_factory=list, max_length=30)


class QuestionGenerationResponse(BaseModel):
    job_title: str
    company: str
    answers: list[QuestionAnswer] = Field(default_factory=list)


class ApplicationCreate(BaseModel):
    job_id: str = Field(min_length=1, max_length=36)
    status: ApplicationStatus = "saved"
    notes: str = Field(default="", max_length=10000)
    questions_answers: list[QuestionAnswer] = Field(default_factory=list, max_length=50)
    application_url: str = Field(default="", max_length=2000)
    follow_up_date: str = Field(default="", max_length=100)
    recruiter_contact: str = Field(default="", max_length=255)


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = Field(default=None, max_length=10000)
    questions_answers: Optional[list[QuestionAnswer]] = Field(default=None, max_length=50)
    follow_up_date: Optional[str] = Field(default=None, max_length=100)
    recruiter_contact: Optional[str] = Field(default=None, max_length=255)


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    job: Optional[Job] = None
    status: ApplicationStatus
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
    job_url: str = Field(default="", max_length=2000)
    auto_fill: bool = True


class BrowserPrepareResponse(BaseModel):
    status: Literal["PREPARED", "MANUAL_ACTION_REQUIRED", "FAILED"]
    message: str
    detected_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    screenshot_url: Optional[str] = None
    requires_confirmation: bool = True


class BrowserSubmitRequest(BaseModel):
    application_id: str = Field(min_length=1, max_length=36)
    confirmed: bool = False
