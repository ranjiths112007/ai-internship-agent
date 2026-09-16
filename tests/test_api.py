from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ok", "degraded"}
    assert data["database"] == "ok"
    assert "llm_provider" in data


def test_api_profile():
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert "candidate" in data
    assert bool(data["candidate"]["name"])


def test_api_score():
    response = client.post("/api/score", json={
        "title": "AI Engineer Intern", "company": "Nexus AI",
        "description": "RAG, pgvector, FastAPI", "location": "Bengaluru",
        "stipend_monthly_inr": 45000,
    })
    assert response.status_code == 200
    data = response.json()
    assert "score" in data and data["score"]["total"] > 60.0


def test_api_discovery_urls():
    response = client.get("/api/discovery/urls")
    assert response.status_code == 200
    assert isinstance(response.json(), list) and len(response.json()) > 0


def test_api_discovery_run():
    response = client.post("/api/discovery/run")
    assert response.status_code == 200
    data = response.json()
    assert {"sources_checked", "jobs_seen", "new_jobs"}.issubset(data)


def test_api_jobs_list():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_job_lifecycle_and_application_tracking():
    job_payload = {
        "external_id": "api-test-lifecycle-unique",
        "title": "RAG AI Engineer Intern",
        "company": "Lifecycle Test AI",
        "description": "Build Python FastAPI RAG systems with embeddings.",
        "location": "Chennai, India", "country": "India", "work_mode": "onsite",
        "stipend_monthly_inr": 45000, "source": "test",
        "application_url": "https://example.test/apply/lifecycle",
    }
    created = client.post("/api/jobs", json=job_payload)
    assert created.status_code == 201
    job_id = created.json()["id"]

    duplicate = client.post("/api/jobs", json=job_payload)
    assert duplicate.status_code == 201
    assert duplicate.json()["created"] is False
    assert duplicate.json()["id"] == job_id

    application = client.post("/api/applications", json={
        "job_id": job_id, "status": "shortlisted", "notes": "Strong RAG match",
    })
    assert application.status_code == 200
    app_id = application.json()["id"]
    assert application.json()["status"] == "shortlisted"

    patched = client.patch(f"/api/applications/{app_id}", json={
        "status": "applied", "notes": "Submitted manually",
    })
    assert patched.status_code == 200
    assert patched.json()["status"] == "applied"
    assert patched.json()["applied_at"] is not None

    fetched = client.get(f"/api/applications/{app_id}")
    assert fetched.status_code == 200
    assert fetched.json()["job"]["id"] == job_id


def test_api_application_validation_and_missing_resources():
    missing = client.post("/api/applications", json={"job_id": "does-not-exist", "status": "saved"})
    assert missing.status_code == 404
    missing_get = client.get("/api/applications/not-real")
    assert missing_get.status_code == 404


def test_api_invalid_application_status_is_rejected():
    response = client.get("/api/applications", params={"status": "not-a-real-status"})
    assert response.status_code == 400


def test_api_questions_generate():
    response = client.post("/api/applications/questions/generate", json={
        "job_title": "AI Engineer Intern", "company": "HyperScale AI",
        "job_description": "Building RAG and vector search",
        "questions": ["Why do you want to join us?"],
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["answers"]) == 1
    assert "Ranjith" in data["answers"][0]["answer"] or "AI" in data["answers"][0]["answer"]


def test_browser_submit_never_fakes_external_submission():
    response = client.post("/api/browser/submit", json={"application_id": "local-test", "confirmed": True})
    assert response.status_code == 200
    assert response.json()["status"] == "READY_FOR_MANUAL_SUBMISSION"


def test_browser_submit_requires_confirmation():
    response = client.post("/api/browser/submit", json={"application_id": "local-test", "confirmed": False})
    assert response.status_code == 200
    assert response.json()["status"] == "STOPPED"
