from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.db.models import JobModel
from app.models.schemas import ApplicationCreate, ApplicationUpdate
from app.services.application import create_application, get_application, update_application


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_job_and_application_crud(db_session):
    job = JobModel(
        title="Generative AI Intern",
        company="HyperScale AI",
        location="Bengaluru",
        stipend_monthly_inr=50000,
        score_total=85.0
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None

    app_data = ApplicationCreate(job_id=job.id, status="saved", notes="Applied via referral")
    app_res = create_application(db_session, app_data)

    assert app_res.id is not None
    assert app_res.job_id == job.id
    assert app_res.status == "saved"

    updated = update_application(db_session, app_res.id, ApplicationUpdate(status="interview"))
    assert updated is not None
    assert updated.status == "interview"

    fetched = get_application(db_session, app_res.id)
    assert fetched is not None
    assert fetched.status == "interview"
