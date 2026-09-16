from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)
JSEARCH_URL = "https://api.openwebninja.com/jsearch/search-v2"
DEFAULT_QUERIES = (
    "AI Engineer intern",
    "Generative AI intern",
    "Machine Learning Engineer intern",
    "LLM Engineer intern",
)


class JSearchJobSource(JobSource):
    """Real JSearch adapter. Queries are generated from the candidate profile."""

    def __init__(self, name: str = "JSearch API (OpenWebNinja)", api_key: str | None = None,
                 queries: tuple[str, ...] = DEFAULT_QUERIES, timeout: float = 20.0) -> None:
        self.name = name
        self.api_key = api_key if api_key is not None else settings.openwebninja_api_key
        self.queries = queries
        self.timeout = timeout

    @staticmethod
    def _monthly_amount(min_salary: Any, max_salary: Any, period: Any, currency: str) -> int | None:
        values = [value for value in (min_salary, max_salary) if isinstance(value, (int, float))]
        if not values or str(currency).upper() != "INR":
            return None
        amount = max(values)
        period_text = str(period or "").lower()
        if "year" in period_text:
            amount /= 12
        elif "month" not in period_text:
            return None
        return max(0, int(amount))

    def _parse_item(self, item: dict[str, Any]) -> Job | None:
        title = str(item.get("job_title") or "").strip()
        company = str(item.get("employer_name") or "").strip()
        description = str(item.get("job_description") or "").strip()
        application_url = str(item.get("job_apply_link") or item.get("job_google_link") or "").strip()
        external_id = str(item.get("job_id") or "").strip()
        if not title or not company or not application_url:
            return None

        city = str(item.get("job_city") or "").strip()
        state = str(item.get("job_state") or "").strip()
        country = str(item.get("job_country") or "").strip()
        location = ", ".join(part for part in (city, state, country) if part) or "Unknown"
        is_remote = bool(item.get("job_is_remote", False))
        currency = str(item.get("job_salary_currency") or "INR").upper()
        min_salary = item.get("job_min_salary")
        max_salary = item.get("job_max_salary")
        period = item.get("job_salary_period") or ""
        stipend = self._monthly_amount(min_salary, max_salary, period, currency)
        salary_text = ""
        if min_salary is not None or max_salary is not None:
            salary_text = f"{min_salary or max_salary}-{max_salary or min_salary} {period}".strip()

        return Job(
            external_id=external_id, title=title, company=company, description=description[:5000],
            location=location, country=country or "Unknown", work_mode="remote" if is_remote else "onsite",
            stipend_monthly_inr=stipend, salary_text=salary_text, currency=currency, source=self.name,
            application_url=application_url, source_url=application_url,
            posted_date=str(item.get("job_posted_at_datetime_utc") or ""),
            deadline=str(item.get("job_offer_expiration_datetime_utc") or ""),
        )

    def fetch_jobs(self) -> list[Job]:
        if not self.api_key:
            logger.info("Source %s skipped: OPENWEBNINJA_API_KEY is not configured", self.name)
            return []
        jobs: list[Job] = []
        seen: set[str] = set()
        headers = {"X-API-Key": self.api_key, "Accept": "application/json"}
        for query in self.queries:
            try:
                response = httpx.get(JSEARCH_URL, headers=headers,
                                     params={"query": query, "num_pages": 1}, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("Source %s failed for query %r: %s", self.name, query, exc)
                continue
            items = payload.get("data", []) if isinstance(payload, dict) else []
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                try:
                    job = self._parse_item(item)
                except (TypeError, ValueError):
                    continue
                if job is None:
                    continue
                key = job.external_id or job.application_url
                if key and key not in seen:
                    seen.add(key)
                    jobs.append(job)
        return jobs
