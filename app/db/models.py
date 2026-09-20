from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String(255), default="")
    source = Column(String(100), default="unknown")
    title = Column(String(255), nullable=False)
    normalized_title = Column(String(255), default="")
    company = Column(String(255), nullable=False)
    description = Column(Text, default="")
    location = Column(String(255), default="")
    country = Column(String(100), default="India")
    work_mode = Column(String(50), default="unknown")
    remote_category = Column(String(50), default="unknown")
    location_category = Column(String(50), default="unknown")
    employment_type = Column(String(50), default="internship")
    stipend_monthly_inr = Column(Integer, nullable=True)
    salary_text = Column(String(255), default="")
    currency = Column(String(10), default="INR")
    application_url = Column(Text, default="")
    source_url = Column(Text, default="")
    skills_json = Column(Text, default="[]")
    perks_json = Column(Text, default="[]")
    posted_date = Column(String(50), default="")
    deadline = Column(String(50), default="")
    dedup_hash = Column(String(64), index=True, default="")
    score_total = Column(Float, default=0.0)
    score_breakdown_json = Column(Text, default="{}")
    llm_analysis_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    applications = relationship("ApplicationModel", back_populates="job", cascade="all, delete-orphan")


class ApplicationModel(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    status = Column(String(50), default="saved")
    notes = Column(Text, default="")
    questions_answers_json = Column(Text, default="[]")
    application_url = Column(Text, default="")
    applied_at = Column(DateTime, nullable=True)
    follow_up_date = Column(String(50), default="")
    recruiter_contact = Column(String(255), default="")
    source = Column(String(100), default="")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    job = relationship("JobModel", back_populates="applications")
