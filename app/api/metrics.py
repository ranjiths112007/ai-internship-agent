from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import ApplicationModel, JobModel
from app.db.session import get_db

router = APIRouter(tags=["dashboard"])


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)) -> dict[str, object]:
    """Return dashboard aggregates directly from persisted data."""
    total_jobs = db.query(func.count(JobModel.id)).scalar() or 0
    high_fit = db.query(func.count(JobModel.id)).filter(JobModel.score_total >= 70).scalar() or 0
    international = (
        db.query(func.count(JobModel.id))
        .filter(JobModel.location_category == "international_remote")
        .scalar()
        or 0
    )
    total_applications = db.query(func.count(ApplicationModel.id)).scalar() or 0

    rows = (
        db.query(ApplicationModel.status, func.count(ApplicationModel.id))
        .group_by(ApplicationModel.status)
        .all()
    )
    applications_by_status = {str(status): int(count) for status, count in rows}

    return {
        "jobs": {
            "total": int(total_jobs),
            "high_fit": int(high_fit),
            "international_remote": int(international),
        },
        "applications": {
            "total": int(total_applications),
            "by_status": applications_by_status,
        },
    }
