from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models import ApplicationModel, JobModel
from app.models.schemas import (
    ApplicationCreate, ApplicationResponse, ApplicationUpdate, Job,
    QuestionAnswer, QuestionGenerationRequest, QuestionGenerationResponse
)
from app.services.llm import get_llm_provider
from app.services.scoring import load_profile

logger = logging.getLogger(__name__)


def generate_application_answers(req: QuestionGenerationRequest) -> QuestionGenerationResponse:
    profile = load_profile()
    llm = get_llm_provider()

    questions = req.questions
    if not questions:
        questions = [
            "Why do you want to join us as an AI Intern?",
            "Tell us about a technical AI/LLM project you built.",
            "What are your stipend expectations?",
            "What is your availability and location preference?"
        ]

    answers = llm.generate_application_answers(
        job_title=req.job_title or "AI Engineer Intern",
        company=req.company or "Tech Company",
        jd_text=req.job_description or "",
        profile=profile,
        questions=questions
    )

    return QuestionGenerationResponse(
        job_title=req.job_title or "AI Engineer Intern",
        company=req.company or "Tech Company",
        answers=answers
    )


def _to_application_response(app_model: ApplicationModel, job_model: Optional[JobModel] = None) -> ApplicationResponse:
    qa_list = []
    if app_model.questions_answers_json:
        try:
            raw_qa = json.loads(app_model.questions_answers_json)
            qa_list = [QuestionAnswer(**item) for item in raw_qa]
        except Exception:
            qa_list = []

    job_schema = None
    target_job = job_model or app_model.job
    if target_job:
        skills = json.loads(target_job.skills_json) if target_job.skills_json else []
        perks = json.loads(target_job.perks_json) if target_job.perks_json else []
        job_schema = Job(
            id=target_job.id,
            external_id=target_job.external_id,
            title=target_job.title,
            normalized_title=target_job.normalized_title,
            company=target_job.company,
            description=target_job.description,
            location=target_job.location,
            country=target_job.country,
            work_mode=target_job.work_mode,
            remote_category=target_job.remote_category,
            location_category=target_job.location_category,
            employment_type=target_job.employment_type,
            stipend_monthly_inr=target_job.stipend_monthly_inr,
            salary_text=target_job.salary_text,
            currency=target_job.currency,
            source=target_job.source,
            application_url=target_job.application_url,
            source_url=target_job.source_url,
            skills=skills,
            perks=perks,
            posted_date=target_job.posted_date,
            deadline=target_job.deadline,
            dedup_hash=target_job.dedup_hash,
        )

    return ApplicationResponse(
        id=app_model.id,
        job_id=app_model.job_id,
        job=job_schema,
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


def create_application(db: Session, data: ApplicationCreate) -> ApplicationResponse:
    job = db.query(JobModel).filter(JobModel.id == data.job_id).first()
    if not job:
        raise ValueError(f"Job with ID {data.job_id} not found.")

    qa_json = json.dumps([qa.model_dump() for qa in data.questions_answers])
    app_model = ApplicationModel(
        job_id=data.job_id,
        status=data.status,
        notes=data.notes,
        questions_answers_json=qa_json,
        application_url=data.application_url or job.application_url,
        follow_up_date=data.follow_up_date,
        recruiter_contact=data.recruiter_contact,
        source=job.source,
    )
    if data.status == "applied":
        app_model.applied_at = datetime.now(timezone.utc)

    db.add(app_model)
    db.commit()
    db.refresh(app_model)
    return _to_application_response(app_model, job)


def get_application(db: Session, application_id: str) -> Optional[ApplicationResponse]:
    app_model = db.query(ApplicationModel).filter(ApplicationModel.id == application_id).first()
    if not app_model:
        return None
    return _to_application_response(app_model)


def list_applications(db: Session, status: Optional[str] = None) -> list[ApplicationResponse]:
    query = db.query(ApplicationModel)
    if status:
        query = query.filter(ApplicationModel.status == status)
    app_models = query.order_by(ApplicationModel.created_at.desc()).all()
    return [_to_application_response(app) for app in app_models]


def update_application(db: Session, application_id: str, data: ApplicationUpdate) -> Optional[ApplicationResponse]:
    app_model = db.query(ApplicationModel).filter(ApplicationModel.id == application_id).first()
    if not app_model:
        return None

    if data.status is not None:
        old_status = app_model.status
        app_model.status = data.status
        if data.status == "applied" and old_status != "applied":
            app_model.applied_at = datetime.now(timezone.utc)
    if data.notes is not None:
        app_model.notes = data.notes
    if data.questions_answers is not None:
        app_model.questions_answers_json = json.dumps([qa.model_dump() for qa in data.questions_answers])
    if data.follow_up_date is not None:
        app_model.follow_up_date = data.follow_up_date
    if data.recruiter_contact is not None:
        app_model.recruiter_contact = data.recruiter_contact

    db.commit()
    db.refresh(app_model)
    return _to_application_response(app_model)
