from fastapi import APIRouter

from app.models.schemas import Job, ScoredJob
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
