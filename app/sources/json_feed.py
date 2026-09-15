from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)


class JSONFeedJobSource(JobSource):
    """Generic JSON job feed adapter with conservative field handling."""

    def __init__(self, name: str, url: str, items_key: str | None = None, timeout: float = 15.0):
        self.name = name
        self.url = url
        self.items_key = items_key
        self.timeout = timeout

    @staticmethod
    def _first(item: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                return value
        return None

    def _parse_item(self, item: dict[str, Any]) -> Job | None:
        title = str(self._first(item, "title", "job_title", "role", "position") or "").strip()
        company = str(self._first(item, "company", "company_name", "employer", "employer_name") or "").strip()
        application_url = str(self._first(item, "apply_url", "application_url", "url", "link") or "").strip()
        if not title or not company or not application_url:
            return None

        description = str(self._first(item, "description", "job_description", "details") or "").strip()
        location = str(self._first(item, "location", "city", "job_city") or "Unknown").strip()
        country = str(self._first(item, "country", "job_country") or "Unknown").strip()
        work_mode = str(self._first(item, "work_mode", "remote", "workplace_type") or "unknown").strip()
        currency = str(self._first(item, "currency", "salary_currency") or "INR").upper()
        stipend_raw = self._first(item, "stipend_monthly_inr", "monthly_stipend", "stipend")
        stipend = None
        if isinstance(stipend_raw, (int, float)) and stipend_raw >= 0:
            stipend = int(stipend_raw)
        elif isinstance(stipend_raw, str):
            try:
                stipend = int(float(stipend_raw.replace(",", "").strip()))
            except ValueError:
                pass

        skills = self._first(item, "skills", "required_skills") or []
        if isinstance(skills, str):
            skills = [part.strip() for part in skills.split(",") if part.strip()]
        if not isinstance(skills, list):
            skills = []

        return Job(
            external_id=str(self._first(item, "id", "job_id", "external_id") or "").strip(),
            title=title[:255],
            company=company[:255],
            description=description[:5000],
            location=location[:255],
            country=country[:100],
            work_mode=work_mode[:50],
            stipend_monthly_inr=stipend if currency == "INR" else None,
            salary_text=str(self._first(item, "salary", "salary_text") or ""),
            currency=currency[:10],
            source=self.name,
            application_url=application_url,
            source_url=str(self._first(item, "source_url", "url", "link") or application_url),
            skills=[str(x) for x in skills if str(x).strip()][:50],
            posted_date=str(self._first(item, "posted_date", "date_posted", "published_at") or ""),
            deadline=str(self._first(item, "deadline", "application_deadline") or ""),
        )

    def fetch_jobs(self) -> list[Job]:
        try:
            response = httpx.get(
                self.url,
                headers={"User-Agent": "AI-Internship-Agent/1.0", "Accept": "application/json"},
                timeout=self.timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("JSON source %s failed: %s", self.name, exc)
            return []

        items: Any = data.get(self.items_key, []) if self.items_key and isinstance(data, dict) else data
        if not isinstance(items, list):
            logger.warning("JSON source %s returned a non-list feed", self.name)
            return []

        jobs: list[Job] = []
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                job = self._parse_item(item)
            except (TypeError, ValueError) as exc:
                logger.warning("JSON source %s skipped malformed item: %s", self.name, exc)
                continue
            if job is None:
                continue
            key = job.external_id or job.application_url
            if key in seen:
                continue
            seen.add(key)
            jobs.append(job)
        return jobs
