from __future__ import annotations

import httpx

from app.sources.jsearch import JSearchJobSource


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "request failed",
                request=httpx.Request("GET", "https://example.test"),
                response=httpx.Response(self.status_code),
            )

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_jsearch_skips_without_api_key():
    source = JSearchJobSource(api_key="")
    assert source.fetch_jobs() == []


def test_jsearch_parses_and_deduplicates(monkeypatch):
    calls = []
    payload = {
        "data": [
            {
                "job_id": "abc",
                "job_title": "AI Engineer Intern",
                "employer_name": "Example AI",
                "job_description": "Build RAG systems.",
                "job_city": "Bengaluru",
                "job_state": "Karnataka",
                "job_country": "India",
                "job_is_remote": False,
                "job_min_salary": 360000,
                "job_max_salary": 480000,
                "job_salary_currency": "INR",
                "job_salary_period": "YEAR",
                "job_apply_link": "https://example.test/apply/abc",
                "job_posted_at_datetime_utc": "2026-09-14T00:00:00Z",
                "job_offer_expiration_datetime_utc": "2026-10-01T00:00:00Z",
            },
            {
                "job_id": "abc",
                "job_title": "AI Engineer Intern",
                "employer_name": "Example AI",
                "job_apply_link": "https://example.test/apply/abc",
            },
            {
                "job_id": "missing-url",
                "job_title": "Incomplete",
                "employer_name": "Example AI",
            },
        ]
    }

    def fake_get(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeResponse(payload)

    monkeypatch.setattr("app.sources.jsearch.httpx.get", fake_get)
    source = JSearchJobSource(api_key="test-key", queries=("AI intern", "AI intern 2"))
    jobs = source.fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].external_id == "abc"
    assert jobs[0].company == "Example AI"
    assert jobs[0].stipend_monthly_inr == 40000
    assert jobs[0].currency == "INR"
    assert jobs[0].deadline.startswith("2026-10-01")
    assert len(calls) == 2


def test_jsearch_does_not_fake_non_inr_salary(monkeypatch):
    payload = {
        "data": [
            {
                "job_id": "us-1",
                "job_title": "ML Intern",
                "employer_name": "Global AI",
                "job_country": "United States",
                "job_is_remote": True,
                "job_min_salary": 50000,
                "job_max_salary": 70000,
                "job_salary_currency": "USD",
                "job_salary_period": "YEAR",
                "job_apply_link": "https://example.test/apply/us-1",
            }
        ]
    }
    monkeypatch.setattr("app.sources.jsearch.httpx.get", lambda *a, **k: FakeResponse(payload))

    job = JSearchJobSource(api_key="test-key", queries=("ML intern",)).fetch_jobs()[0]
    assert job.currency == "USD"
    assert job.stipend_monthly_inr is None


def test_jsearch_isolates_http_failures(monkeypatch):
    def fake_get(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr("app.sources.jsearch.httpx.get", fake_get)
    source = JSearchJobSource(api_key="test-key", queries=("AI intern",))
    assert source.fetch_jobs() == []


def test_jsearch_handles_bad_json(monkeypatch):
    monkeypatch.setattr(
        "app.sources.jsearch.httpx.get",
        lambda *a, **k: FakeResponse(payload=ValueError("bad json")),
    )
    source = JSearchJobSource(api_key="test-key", queries=("AI intern",))
    assert source.fetch_jobs() == []


def test_jsearch_handles_http_error(monkeypatch):
    monkeypatch.setattr(
        "app.sources.jsearch.httpx.get",
        lambda *a, **k: FakeResponse(payload={}, status_code=429),
    )
    source = JSearchJobSource(api_key="test-key", queries=("AI intern",))
    assert source.fetch_jobs() == []
