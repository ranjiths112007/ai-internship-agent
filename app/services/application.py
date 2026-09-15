from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import ApplicationModel, JobModel
from app.models.schemas import (
    ApplicationCreate, ApplicationResponse, ApplicationUpdate, Job,
    QuestionAnswer, QuestionGenerationRequest, QuestionGenerationResponse,
)
from app.services.llm import get_llm_provider
from app.services.scoring import load_profile

logger = logging.getLogger(__name__)

APPLICATION_STATUSES = {
    "saved", "discovered", "shortlisted", "applying", "applied",
    "assessment", "interview", "rejected", "offer", "withdrawn",
}

DEFAULT_QUESTIONS = (
    "Why do you want to join us as an AI Intern?",
    "Tell us about a technical AI/LLM project you built.",
    "What are your stipend expectations?",
    "What is your availability and location preference?",
)


def generate_application_answers(req: QuestionGenerationRequest) -> QuestionGenerationResponse:
    profile = load_profile()
    llm = get_llm_provider()
    questions = req.questions or list(DEFAULT_QUESTIONS)
    answers = llm.generate_application_answers(
        job_title=req.job_title or "AI Engineer Intern",
        company=req.company or "Company",
        jd_text=req.job_description or "",
        profile=profile,
        questions=questions,
    )
    return QuestionGenerationResponse(
        job_title=req.job_title or "AI Engineer Intern",
        company=req.company or "Company",
        answers=answers,
    )


def _safe_json(value: str | None, default):
    if not value:
        return default
    try:
        parsed = json.loads(value)
        return parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _job_schema(job: JobModel | None) -> Job | None:
    if not job:
        return None
    return Job(
        id=job.id,
        external_id=job.external_id,
        title=job.title,
        normalized_title=job.normalized_title,
        company=job.company,
        description=job.description,
        location=job.location,
        country=job.country,
        work_mode=job.work_mode,
        remote_category=job.remote_category,
        location_category=job.location_category,
        employment_type=job.employment_type,
        stipend_monthly_inr=job.stipend_monthly_inr,
        salary_text=job.salary_text,
        currency=job.currency,
        source=job.source,
        application_url=job.application_url,
        source_url=job.source_url,
        skills=_safe_json(job.skills_json, []),
        perks=_safe_json(job.perks_json, []),
        posted_date=job.posted_date,
        deadline=job.deadline,
        dedup_hash=job.dedup_hash,
    )


def _to_application_response(app_model: ApplicationModel, job_model: Optional[JobModel] = None) -> ApplicationResponse:
    raw_qa = _safe_json(app_model.questions_answers_json, [])
    qa_list = []
    if isinstance(raw_qa, list):
        for item in raw_qa:
            if isinstance(item, dict):
                try:
                    qa_list.append(QuestionAnswer(**item))
                except Exception:
                    continue
    target_job = job_model or app_model.job
    return ApplicationResponse(
        id=app_model.id,
        job_id=app_model.job_id,
        job=_job_schema(target_job),
        status=app_model.status,
        notes=app_model.notes or "",
        questions_answers=qa_list,
        application_url=app_model.application_url or "",
        applied_at=app_model.applied_at.isoformat() if app_model.applied_at else None,
        follow_up_date=app_model.follow_up_date or "",
        recruiter_contact=app_model.recruiter_contact or "",
        source=app_model.source or "",
        created_at=app_model.created_at.isoformat() if app_model.created_at else "",
        updated_at=app_model.updated_at.isoformat() if app_model.updated_at else "",
    )


def _validate_status(status: str) -> str:
    value = status.strip().lower()
    if value not in APPLICATION_STATUSES:
        raise ValueError(f"Invalid application status: {status}. Allowed: {', '.join(sorted(APPLICATION_STATUSES))}")
    return value


def create_application(db: Session, data: ApplicationCreate) -> ApplicationResponse:
    job = db.query(JobModel).filter(JobModel.id == data.job_id).first()
    if not job:
        raise ValueError(f"Job with ID {data.job_id} not found.")
    status = _validate_status(data.status)
    app_model = ApplicationModel(
        job_id=job.id,
        status=status,
        notes=data.notes.strip(),
        questions_answers_json=json.dumps([qa.model_dump() for qa in data.questions_answers]),
        application_url=data.application_url.strip() or job.application_url,
        follow_up_date=data.follow_up_date.strip(),
        recruiter_contact=data.recruiter_contact.strip(),
        source=job.source,
    )
    if status == "applied":
        app_model.applied_at = datetime.now(timezone.utc)
    try:
        db.add(app_model)
        db.commit()
        db.refresh(app_model)
    except Exception:
        db.rollback()
        logger.exception("Failed to create application for job %s", job.id)
        raise
    return _to_application_response(app_model, job)


def get_application(db: Session, application_id: str) -> Optional[ApplicationResponse]:
    app_model = db.query(ApplicationModel).filter(ApplicationModel.id == application_id).first()
    return _to_application_response(app_model) if app_model else None


def list_applications(db: Session, status: Optional[str] = None) -> list[ApplicationResponse]:
    query = db.query(ApplicationModel)
    if status:
        query = query.filter(ApplicationModel.status == _validate_status(status))
    return [_to_application_response(app) for app in query.order_by(ApplicationModel.created_at.desc()).all()]


def update_application(db: Session, application_id: str, data: ApplicationUpdate) -> Optional[ApplicationResponse]:
    app_model = db.query(ApplicationModel).filter(ApplicationModel.id == application_id).first()
    if not app_model:
        return None

    if data.status is not None:
        new_status = _validate_status(data.status)
        old_status = app_model.status
        app_model.status = new_status
        if new_status == "applied" and old_status != "applied":
            app_model.applied_at = datetime.now(timezone.utc)
        elif new_status != "applied" and old_status == "applied":
            # Preserve the audit timestamp; changing state should not erase history.
            pass
    if data.notes is not None:
        app_model.notes = data.notes
    if data.questions_answers is not None:
        app_model.questions_answers_json = json.dumps([qa.model_dump() for qa in data.questions_answers])
    if data.follow_up_date is not None:
        app_model.follow_up_date = data.follow_up_date
    if data.recruiter_contact is not None:
        app_model.recruiter_contact = data.recruiter_contact

    try:
        db.commit()
        db.refresh(app_model)
    except Exception:
        db.rollback()
        logger.exception("Failed to update application %s", application_id)
        raise
    return _to_application_response(app_model)
