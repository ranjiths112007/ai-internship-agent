from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.browser.application_runner import prepare_application_workflow, submit_application_workflow
from app.core.config import settings
from app.db.models import JobModel
from app.db.session import get_db
from app.models.schemas import ApplicationCreate, ApplicationResponse, ApplicationUpdate, BrowserPrepareRequest, BrowserPrepareResponse, BrowserSubmitRequest, DiscoveryRunResult, Job, JobAnalysisResult, QuestionGenerationRequest, QuestionGenerationResponse, ScoredJob
from app.services.application import create_application, generate_application_answers, get_application, list_applications, update_application
from app.services.deduplication import compute_dedup_hash
from app.services.discovery import build_search_urls, run_discovery_pipeline
from app.services.llm import get_llm_provider
from app.services.normalization import normalize_job
from app.services.scoring import load_profile, score_job

router = APIRouter()


def _json_list(value: Optional[str]) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _json_dict(value: Optional[str]) -> dict:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    return {"status": "ok" if database == "ok" else "degraded", "database": database, "llm_provider": get_llm_provider().__class__.__name__, "scheduler": "enabled" if settings.discovery_enabled else "disabled"}


@router.get("/profile")
def profile() -> dict:
    return load_profile()


@router.post("/score", response_model=ScoredJob)
def score(job: Job) -> ScoredJob:
    normalized = normalize_job(job)
    return ScoredJob(job=normalized, score=score_job(normalized))


@router.get("/discovery/urls")
def discovery_urls() -> list[dict[str, str]]:
    profile_data = load_profile()
    return build_search_urls(profile_data.get("target_roles", []), profile_data.get("locations", []))


@router.post("/discovery/run", response_model=DiscoveryRunResult)
def run_discovery(db: Session = Depends(get_db)) -> DiscoveryRunResult:
    try:
        return run_discovery_pipeline(db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Discovery pipeline failed: {exc}") from exc


@router.get("/jobs")
def get_jobs(min_score: float = Query(0.0, ge=0.0, le=100.0), location: Optional[str] = Query(None, max_length=255), remote_only: bool = False, international_only: bool = False, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    query = db.query(JobModel).filter(JobModel.score_total >= min_score)
    if remote_only:
        query = query.filter(JobModel.work_mode.ilike("%remote%"))
    if international_only:
        query = query.filter(JobModel.location_category == "international_remote")
    if location:
        query = query.filter(JobModel.location.ilike(f"%{location}%"))
    jobs_models = query.order_by(JobModel.score_total.desc(), JobModel.created_at.desc()).limit(limit).all()
    return [{"id": j.id, "external_id": j.external_id, "title": j.title, "company": j.company, "description": j.description, "location": j.location, "country": j.country, "work_mode": j.work_mode, "remote_category": j.remote_category, "location_category": j.location_category, "stipend_monthly_inr": j.stipend_monthly_inr, "salary_text": j.salary_text, "currency": j.currency, "source": j.source, "application_url": j.application_url, "skills": _json_list(j.skills_json), "perks": _json_list(j.perks_json), "posted_date": j.posted_date, "deadline": j.deadline, "score_total": j.score_total, "score_breakdown": _json_dict(j.score_breakdown_json)} for j in jobs_models]


@router.post("/jobs", status_code=201)
def create_job(job: Job, db: Session = Depends(get_db)):
    normalized = normalize_job(job)
    normalized.dedup_hash = compute_dedup_hash(normalized)
    existing = db.query(JobModel).filter(JobModel.dedup_hash == normalized.dedup_hash).first()
    if existing:
        return {"id": existing.id, "title": existing.title, "score_total": existing.score_total, "created": False}
    score_breakdown = score_job(normalized)
    db_job = JobModel(external_id=normalized.external_id, source=normalized.source, title=normalized.title, normalized_title=normalized.normalized_title, company=normalized.company, description=normalized.description, location=normalized.location, country=normalized.country, work_mode=normalized.work_mode, remote_category=normalized.remote_category, location_category=normalized.location_category, employment_type=normalized.employment_type, stipend_monthly_inr=normalized.stipend_monthly_inr, salary_text=normalized.salary_text, currency=normalized.currency, application_url=normalized.application_url, source_url=normalized.source_url, skills_json=json.dumps(normalized.skills), perks_json=json.dumps(normalized.perks), posted_date=normalized.posted_date, deadline=normalized.deadline, dedup_hash=normalized.dedup_hash, score_total=score_breakdown.total, score_breakdown_json=json.dumps(score_breakdown.model_dump()))
    db.add(db_job)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Job already exists or violates a database constraint.") from exc
    db.refresh(db_job)
    return {"id": db_job.id, "title": db_job.title, "score_total": db_job.score_total, "created": True}


@router.get("/jobs/{id}")
def get_job_detail(id: str, db: Session = Depends(get_db)):
    job_model = db.query(JobModel).filter(JobModel.id == id).first()
    if not job_model:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job_model.id, "external_id": job_model.external_id, "title": job_model.title, "company": job_model.company, "description": job_model.description, "location": job_model.location, "country": job_model.country, "work_mode": job_model.work_mode, "remote_category": job_model.remote_category, "location_category": job_model.location_category, "stipend_monthly_inr": job_model.stipend_monthly_inr, "salary_text": job_model.salary_text, "currency": job_model.currency, "source": job_model.source, "application_url": job_model.application_url, "skills": _json_list(job_model.skills_json), "perks": _json_list(job_model.perks_json), "posted_date": job_model.posted_date, "deadline": job_model.deadline, "score_total": job_model.score_total, "score_breakdown": _json_dict(job_model.score_breakdown_json), "llm_analysis": _json_dict(job_model.llm_analysis_json)}


@router.post("/analyze/job", response_model=JobAnalysisResult)
def analyze_job(job: Job):
    return get_llm_provider().analyze_job_description(normalize_job(job))


@router.post("/applications", response_model=ApplicationResponse)
def create_app(data: ApplicationCreate, db: Session = Depends(get_db)):
    if not db.query(JobModel).filter(JobModel.id == data.job_id).first():
        raise HTTPException(status_code=404, detail=f"Job with ID {data.job_id} not found.")
    try:
        return create_application(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/applications", response_model=list[ApplicationResponse])
def get_apps(status: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        return list_applications(db, status=status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/applications/{id}", response_model=ApplicationResponse)
def get_app_detail(id: str, db: Session = Depends(get_db)):
    result = get_application(db, id)
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result


@router.patch("/applications/{id}", response_model=ApplicationResponse)
def update_app_route(id: str, data: ApplicationUpdate, db: Session = Depends(get_db)):
    try:
        result = update_application(db, id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result


@router.post("/applications/questions/generate", response_model=QuestionGenerationResponse)
def generate_questions(req: QuestionGenerationRequest):
    return generate_application_answers(req)


@router.post("/browser/prepare", response_model=BrowserPrepareResponse)
def prepare_browser(req: BrowserPrepareRequest):
    return prepare_application_workflow(req)


@router.post("/browser/submit")
def submit_browser(req: BrowserSubmitRequest):
    return submit_application_workflow(req)
