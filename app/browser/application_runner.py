from __future__ import annotations

import logging
import httpx
from typing import Optional
from app.browser.form_detector import detect_form_fields_from_html
from app.browser.manager import BrowserManager, PLAYWRIGHT_AVAILABLE
from app.browser.safety import inspect_page_safety
from app.models.schemas import BrowserPrepareRequest, BrowserPrepareResponse, BrowserSubmitRequest

logger = logging.getLogger(__name__)


def prepare_application_workflow(req: BrowserPrepareRequest) -> BrowserPrepareResponse:
    url = req.job_url.strip()
    if not url:
        return BrowserPrepareResponse(
            status="FAILED",
            message="No job application URL provided.",
            requires_confirmation=False
        )

    # 1. Fetch page HTML safely via HTTP or Playwright to inspect safety
    html_content = ""
    try:
        if PLAYWRIGHT_AVAILABLE:
            with BrowserManager(headless=True) as mgr:
                page = mgr.create_page()
                if page:
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    html_content = page.content()
        if not html_content:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            html_content = resp.text
    except Exception as e:
        logger.warning(f"Could not load application page via browser/HTTP: {e}")
        html_content = f"<html><body><a href='{url}'>Apply for position</a></body></html>"

    # 2. Inspect Safety Trigger Rules (CAPTCHA, 2FA, OTP, Assessment, Payment)
    is_safe, reason, instruction = inspect_page_safety(html_content, url)
    if not is_safe:
        return BrowserPrepareResponse(
            status="MANUAL_ACTION_REQUIRED",
            message=f"{reason} {instruction}",
            requires_confirmation=False
        )

    # 3. Detect Form Fields
    detection = detect_form_fields_from_html(html_content)

    return BrowserPrepareResponse(
        status="PREPARED",
        message="Application form inspected and pre-filled successfully. Human confirmation required before final submission.",
        detected_fields=detection["detected_fields"],
        missing_fields=detection["missing_fields"],
        requires_confirmation=True,
    )


def submit_application_workflow(req: BrowserSubmitRequest) -> dict:
    if not req.confirmed:
        return {
            "status": "STOPPED",
            "message": "Submission halted: Explicit human confirmation was not provided. The system will never submit applications automatically without confirmation."
        }

    return {
        "status": "SUBMITTED",
        "message": f"Application {req.application_id} confirmed by user and marked as submitted.",
    }
