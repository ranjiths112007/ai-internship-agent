from __future__ import annotations

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import JobModel
from app.db.session import get_db
from app.models.schemas import (
    ApplicationCreate, ApplicationResponse, ApplicationUpdate,
    BrowserPrepareRequest, BrowserPrepareResponse, BrowserSubmitRequest,
    DiscoveryRunResult, Job, JobAnalysisResult, QuestionGenerationRequest,
    QuestionGenerationResponse, ScoreBreakdown, ScoredJob
)
from app.browser.application_runner import prepare_application_workflow, submit_application_workflow
from app.services.application import (
    create_application, generate_application_answers, get_application,
    list_applications, update_application
)
from app.services.discovery import build_search_urls, run_discovery_pipeline
from app.services.llm import get_llm_provider
from app.services.normalization import normalize_job
from app.services.scoring import load_profile, score_job

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/profile")
def profile() -> dict:
    return load_profile()


@router.post("/score", response_model=ScoredJob)
def score(job: Job) -> ScoredJob:
    norm_job = normalize_job(job)
    return ScoredJob(job=norm_job, score=score_job(norm_job))


@router.get("/discovery/urls")
def discovery_urls() -> list[dict[str, str]]:
    profile_data = load_profile()
    return build_search_urls(profile_data["target_roles"], profile_data["locations"])


@router.post("/discovery/run", response_model=DiscoveryRunResult)
def run_discovery(db: Session = Depends(get_db)) -> DiscoveryRunResult:
    return run_discovery_pipeline(db)


@router.get("/jobs")
def get_jobs(
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    location: Optional[str] = None,
    remote_only: bool = False,
    international_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(JobModel).filter(JobModel.score_total >= min_score)

    if remote_only:
        query = query.filter(JobModel.work_mode.ilike("%remote%"))
    if international_only:
        query = query.filter(JobModel.location_category == "international_remote")
    if location:
        query = query.filter(JobModel.location.ilike(f"%{location}%"))

    jobs_models = query.order_by(JobModel.score_total.desc()).limit(limit).all()

    results = []
    for j in jobs_models:
        skills = json.loads(j.skills_json) if j.skills_json else []
        perks = json.loads(j.perks_json) if j.perks_json else []
        score_bd = json.loads(j.score_breakdown_json) if j.score_breakdown_json else {}

        results.append({
            "id": j.id,
            "external_id": j.external_id,
            "title": j.title,
            "company": j.company,
            "description": j.description,
            "location": j.location,
            "country": j.country,
            "work_mode": j.work_mode,
            "remote_category": j.remote_category,
            "location_category": j.location_category,
            "stipend_monthly_inr": j.stipend_monthly_inr,
            "salary_text": j.salary_text,
            "currency": j.currency,
            "source": j.source,
            "application_url": j.application_url,
            "skills": skills,
            "perks": perks,
            "posted_date": j.posted_date,
            "score_total": j.score_total,
            "score_breakdown": score_bd,
        })
    return results


@router.post("/jobs")
def create_job(job: Job, db: Session = Depends(get_db)):
    norm_job = normalize_job(job)
    score_bd = score_job(norm_job)

    db_job = JobModel(
        external_id=norm_job.external_id,
        source=norm_job.source,
        title=norm_job.title,
        normalized_title=norm_job.normalized_title,
        company=norm_job.company,
        description=norm_job.description,
        location=norm_job.location,
        country=norm_job.country,
        work_mode=norm_job.work_mode,
        remote_category=norm_job.remote_category,
        location_category=norm_job.location_category,
        employment_type=norm_job.employment_type,
        stipend_monthly_inr=norm_job.stipend_monthly_inr,
        salary_text=norm_job.salary_text,
        currency=norm_job.currency,
        application_url=norm_job.application_url,
        source_url=norm_job.source_url,
        skills_json=json.dumps(norm_job.skills),
        perks_json=json.dumps(norm_job.perks),
        posted_date=norm_job.posted_date,
        dedup_hash=norm_job.dedup_hash,
        score_total=score_bd.total,
        score_breakdown_json=json.dumps(score_bd.model_dump()),
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return {"id": db_job.id, "title": db_job.title, "score_total": db_job.score_total}


@router.get("/jobs/{id}")
def get_job_detail(id: str, db: Session = Depends(get_db)):
    job_model = db.query(JobModel).filter(JobModel.id == id).first()
    if not job_model:
        raise HTTPException(status_code=404, detail="Job not found")

    skills = json.loads(job_model.skills_json) if job_model.skills_json else []
    perks = json.loads(job_model.perks_json) if job_model.perks_json else []
    score_bd = json.loads(job_model.score_breakdown_json) if job_model.score_breakdown_json else {}
    llm_analysis = json.loads(job_model.llm_analysis_json) if job_model.llm_analysis_json else {}

    return {
        "id": job_model.id,
        "external_id": job_model.external_id,
        "title": job_model.title,
        "company": job_model.company,
        "description": job_model.description,
        "location": job_model.location,
        "country": job_model.country,
        "work_mode": job_model.work_mode,
        "remote_category": job_model.remote_category,
        "location_category": job_model.location_category,
        "stipend_monthly_inr": job_model.stipend_monthly_inr,
        "salary_text": job_model.salary_text,
        "currency": job_model.currency,
        "source": job_model.source,
        "application_url": job_model.application_url,
        "skills": skills,
        "perks": perks,
        "posted_date": job_model.posted_date,
        "score_total": job_model.score_total,
        "score_breakdown": score_bd,
        "llm_analysis": llm_analysis,
    }


@router.post("/analyze/job", response_model=JobAnalysisResult)
def analyze_job(job: Job):
    llm = get_llm_provider()
    return llm.analyze_job_description(job)


@router.post("/applications", response_model=ApplicationResponse)
def create_app(data: ApplicationCreate, db: Session = Depends(get_db)):
    try:
        return create_application(db, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/applications", response_model=list[ApplicationResponse])
def get_apps(status: Optional[str] = None, db: Session = Depends(get_db)):
    return list_applications(db, status=status)


@router.get("/applications/{id}", response_model=ApplicationResponse)
def get_app_detail(id: str, db: Session = Depends(get_db)):
    app_res = get_application(db, id)
    if not app_res:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_res


@router.patch("/applications/{id}", response_model=ApplicationResponse)
def update_app_route(id: str, data: ApplicationUpdate, db: Session = Depends(get_db)):
    updated = update_application(db, id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated


@router.post("/applications/questions/generate", response_model=QuestionGenerationResponse)
def generate_questions(req: QuestionGenerationRequest):
    return generate_application_answers(req)


@router.post("/browser/prepare", response_model=BrowserPrepareResponse)
def prepare_browser(req: BrowserPrepareRequest):
    return prepare_application_workflow(req)


@router.post("/browser/submit")
def submit_browser(req: BrowserSubmitRequest):
    return submit_application_workflow(req)
