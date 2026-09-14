from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"


def test_api_profile():
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert "candidate" in data
    assert data["candidate"]["name"] == "Ranjith S"


def test_api_score():
    job_payload = {
        "title": "AI Engineer Intern",
        "company": "Nexus AI",
        "description": "RAG, pgvector, FastAPI",
        "location": "Bengaluru",
        "stipend_monthly_inr": 45000
    }
    response = client.post("/api/score", json=job_payload)
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert data["score"]["total"] > 60.0


def test_api_discovery_urls():
    response = client.get("/api/discovery/urls")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_api_discovery_run():
    response = client.post("/api/discovery/run")
    assert response.status_code == 200
    data = response.json()
    assert "sources_checked" in data
    assert data["sources_checked"] > 0
    assert "jobs_seen" in data


def test_api_jobs_list():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_questions_generate():
    payload = {
        "job_title": "AI Engineer Intern",
        "company": "HyperScale AI",
        "job_description": "Building RAG and vector search",
        "questions": ["Why do you want to join us?"]
    }
    response = client.post("/api/applications/questions/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["answers"]) == 1
    assert "Ranjith" in data["answers"][0]["answer"] or "AI" in data["answers"][0]["answer"]
