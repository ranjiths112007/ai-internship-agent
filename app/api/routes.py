from fastapi import APIRouter

from app.models.schemas import Job, ScoredJob
from app.services.discovery import build_search_urls
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
    return ScoredJob(job=job, score=score_job(job))


@router.get("/discovery/urls")
def discovery_urls() -> list[dict[str, str]]:
    profile = load_profile()
    return build_search_urls(profile["target_roles"], profile["locations"])
