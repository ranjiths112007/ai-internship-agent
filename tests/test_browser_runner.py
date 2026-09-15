from __future__ import annotations

from app.browser.application_runner import prepare_application_workflow, submit_application_workflow
from app.models.schemas import BrowserPrepareRequest, BrowserSubmitRequest


def test_prepare_rejects_invalid_url():
    result = prepare_application_workflow(BrowserPrepareRequest(job_url="javascript:alert(1)"))
    assert result.status == "FAILED"
    assert result.requires_confirmation is False


def test_prepare_stops_on_captcha(monkeypatch):
    monkeypatch.setattr(
        "app.browser.application_runner._load_html",
        lambda url: "<html><body><div>captcha verification</div><form></form></body></html>",
    )
    result = prepare_application_workflow(BrowserPrepareRequest(job_url="https://example.test/apply"))
    assert result.status == "MANUAL_ACTION_REQUIRED"
    assert result.requires_confirmation is False


def test_prepare_reports_fields_without_submitting(monkeypatch):
    monkeypatch.setattr(
        "app.browser.application_runner._load_html",
        lambda url: "<html><body><form><label>Email</label><input name='email'></form></body></html>",
    )
    result = prepare_application_workflow(BrowserPrepareRequest(job_url="https://example.test/apply"))
    assert result.status == "PREPARED"
    assert "email" in result.detected_fields
    assert result.requires_confirmation is True


def test_submit_requires_explicit_confirmation():
    stopped = submit_application_workflow(BrowserSubmitRequest(application_id="app-1", confirmed=False))
    assert stopped["status"] == "STOPPED"

    ready = submit_application_workflow(BrowserSubmitRequest(application_id="app-1", confirmed=True))
    assert ready["status"] == "READY_FOR_MANUAL_SUBMISSION"
