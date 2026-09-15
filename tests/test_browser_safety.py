from __future__ import annotations

from app.browser.application_runner import submit_application_workflow
from app.browser.safety import inspect_page_safety
from app.models.schemas import BrowserSubmitRequest


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
    assert "MANUAL_ACTION_REQUIRED" in instr


def test_browser_safety_clean_page():
    html = "<html><body><form><label>First Name</label><input name='fname'/><label>Email</label></form></body></html>"
    is_safe, reason, instr = inspect_page_safety(html)
    assert is_safe is True
    assert reason == ""
    assert instr == ""


def test_browser_safety_assessment_detection():
    is_safe, reason, _ = inspect_page_safety("<html>Complete your HackerRank technical assessment</html>")
    assert is_safe is False
    assert "assessment" in reason.lower()


def test_browser_safety_sensitive_payment_detection():
    is_safe, reason, _ = inspect_page_safety("<label>Credit Card Number</label><input name='card'>")
    assert is_safe is False
    assert "Sensitive" in reason


def test_submit_without_human_confirmation_stops():
    res = submit_application_workflow(BrowserSubmitRequest(application_id="app-123", confirmed=False))
    assert res["status"] == "STOPPED"
    assert "confirmation was not provided" in res["message"]


def test_confirmed_submit_is_manual_not_fake_submission():
    res = submit_application_workflow(BrowserSubmitRequest(application_id="app-123", confirmed=True))
    assert res["status"] == "READY_FOR_MANUAL_SUBMISSION"
    assert "does not claim or simulate" in res["message"]


def test_browser_safety_url_can_trigger_captcha():
    is_safe, reason, _ = inspect_page_safety("<html>Apply</html>", "https://example.com/cf-challenge")
    assert is_safe is False
    assert "CAPTCHA" in reason
