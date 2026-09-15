from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

from app.browser.form_detector import detect_form_fields_from_html
from app.browser.manager import BrowserManager, PLAYWRIGHT_AVAILABLE
from app.browser.safety import inspect_page_safety
from app.core.config import settings
from app.models.schemas import BrowserPrepareRequest, BrowserPrepareResponse, BrowserSubmitRequest

logger = logging.getLogger(__name__)


def _valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def _load_html(url: str) -> str:
    if PLAYWRIGHT_AVAILABLE:
        try:
            with BrowserManager(headless=settings.playwright_headless) as manager:
                page = manager.create_page()
                if page:
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    return page.content()
        except Exception as exc:
            logger.warning("Playwright could not inspect application page: %s", exc)

    try:
        response = httpx.get(
            url,
            headers={"User-Agent": "AI-Internship-Agent/1.0"},
            timeout=10.0,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as exc:
        logger.warning("HTTP inspection failed for application page: %s", exc)
        return ""


def prepare_application_workflow(req: BrowserPrepareRequest) -> BrowserPrepareResponse:
    url = req.job_url.strip()
    if not url:
        return BrowserPrepareResponse(
            status="FAILED",
            message="No job application URL provided.",
            requires_confirmation=False,
        )
    if not _valid_http_url(url):
        return BrowserPrepareResponse(
            status="FAILED",
            message="Invalid application URL. Only http:// and https:// URLs are supported.",
            requires_confirmation=False,
        )

    html_content = _load_html(url)
    if not html_content:
        return BrowserPrepareResponse(
            status="FAILED",
            message="Could not inspect the application page. No form data was fabricated and no automation was attempted.",
            requires_confirmation=False,
        )

    is_safe, reason, instruction = inspect_page_safety(html_content, url)
    if not is_safe:
        return BrowserPrepareResponse(
            status="MANUAL_ACTION_REQUIRED",
            message=f"{reason} {instruction}",
            requires_confirmation=False,
        )

    detection = detect_form_fields_from_html(html_content)
    return BrowserPrepareResponse(
        status="PREPARED",
        message=(
            "Application form inspected. Safe fields may be prepared, but this endpoint does not submit the application. "
            "Human confirmation is required before any final action."
        ),
        detected_fields=detection["detected_fields"],
        missing_fields=detection["missing_fields"],
        requires_confirmation=True,
    )


def submit_application_workflow(req: BrowserSubmitRequest) -> dict[str, str]:
    """Never performs a real external submission.

    The current MVP has no authenticated submission integration. A confirmed
    request therefore transitions to READY_FOR_MANUAL_SUBMISSION rather than
    falsely claiming that an external website accepted the application.
    """
    if not req.confirmed:
        return {
            "status": "STOPPED",
            "message": "Submission halted: explicit human confirmation was not provided.",
        }

    return {
        "status": "READY_FOR_MANUAL_SUBMISSION",
        "message": (
            f"Application {req.application_id} is confirmed locally. Open the employer portal and submit manually; "
            "the agent does not claim or simulate an external submission."
        ),
    }
