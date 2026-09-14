from __future__ import annotations

from app.browser.safety import inspect_page_safety
from app.browser.application_runner import submit_application_workflow
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


def test_browser_safety_clean_page():
    html = "<html><body><form><label>First Name</label><input name='fname'/><label>Email</label></form></body></html>"
    is_safe, reason, instr = inspect_page_safety(html)

    assert is_safe is True


def test_submit_without_human_confirmation_fails():
    req = BrowserSubmitRequest(application_id="app-123", confirmed=False)
    res = submit_application_workflow(req)

    assert res["status"] == "STOPPED"
    assert "confirmation was not provided" in res["message"]
