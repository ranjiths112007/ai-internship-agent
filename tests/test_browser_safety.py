from __future__ import annotations

from app.browser.application_runner import prepare_application_workflow, submit_application_workflow
from app.browser.safety import inspect_page_safety
from app.models.schemas import BrowserPrepareRequest, BrowserSubmitRequest


def test_browser_safety_captcha_detection():
    html = "<html><body><h1>Apply</h1><div class='g-recaptcha'></div></body></html>"
    is_safe, reason, instr = inspect_page_safety(html)
    assert is_safe is False
    assert "CAPTCHA" in reason
    assert "MANUAL_ACTION_REQUIRED" in instr


def test_browser_safety_otp_detection():
    html = "<html><body><form><label>Enter OTP sent to phone</label></form></body></html>"
    is_safe, reason, instr = inspect_page_safety(html)
    assert is_safe is False
    assert "OTP" in reason


def test_browser_safety_assessment_detection():
    html = "<html><body><h2>Online Assessment</h2><p>Complete this coding test.</p></body></html>"
    is_safe, reason, instr = inspect_page_safety(html)
    assert is_safe is False
    assert "assessment" in reason.lower()


def test_browser_safety_sensitive_payment_detection():
    html = "<html><body><form><label>Credit Card Number</label><input name='card_number'></form></body></html>"
    is_safe, reason, _ = inspect_page_safety(html)
    assert is_safe is False
    assert "payment" in reason.lower() or "sensitive" in reason.lower()


def test_browser_safety_clean_page():
    html = "<html><body><form><label>First Name</label><input name='fname'/><label>Email</label></form></body></html>"
    is_safe, reason, _ = inspect_page_safety(html)
    assert is_safe is True
    assert reason == ""


def test_submit_without_human_confirmation_stops():
    req = BrowserSubmitRequest(application_id="app-123", confirmed=False)
    res = submit_application_workflow(req)
    assert res["status"] == "STOPPED"
    assert "confirmation was not provided" in res["message"]


def test_confirmed_submit_is_manual_not_fake_submission():
    req = BrowserSubmitRequest(application_id="app-123", confirmed=True)
    res = submit_application_workflow(req)
    assert res["status"] == "READY_FOR_MANUAL_SUBMISSION"
    assert "does not claim" in res["message"]


def test_prepare_rejects_invalid_url():
    response = prepare_application_workflow(BrowserPrepareRequest(job_url="javascript:alert(1)"))
    assert response.status == "FAILED"
    assert response.requires_confirmation is False


def test_prepare_requires_manual_confirmation_on_clean_form(monkeypatch):
    monkeypatch.setattr(
        "app.browser.application_runner._load_html",
        lambda url: "<html><body><form><label>First Name</label><input name='fname'><label>Email</label><input name='email'></form></body></html>",
    )
    response = prepare_application_workflow(BrowserPrepareRequest(job_url="https://example.test/apply"))
    assert response.status == "PREPARED"
    assert response.requires_confirmation is True
    assert "first_name" in response.detected_fields
    assert "email" in response.detected_fields
