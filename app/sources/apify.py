from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)

APIFY_BASE_URL = "https://api.apify.com/v2"


class ApifyJobSource(JobSource):
    """Real Apify job scraper source. Uses APIFY_API_KEY and configurable actor tasks."""

    def __init__(
        self,
        name: str = "Apify Jobs Scraper",
        actor_id: str | None = None,
        queries: tuple[str, ...] = ("AI Engineer intern", "Generative AI intern"),
        timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.api_key = settings.apify_api_key
        self.actor_id = actor_id or settings.apify_google_jobs_actor
        self.queries = queries
        self.timeout = timeout
        self.last_status = "Not checked"
        self.last_error = ""

    def _parse_item(self, item: dict[str, Any]) -> Job | None:
        title = str(item.get("title") or item.get("jobTitle") or item.get("position") or "").strip()
        company = str(item.get("company") or item.get("companyName") or item.get("employer") or "").strip()
        description = str(item.get("description") or item.get("jobDescription") or item.get("snippet") or "").strip()
        application_url = str(
            item.get("url") or item.get("jobUrl") or item.get("applyUrl") or item.get("link") or ""
        ).strip()
        external_id = str(item.get("id") or item.get("jobId") or item.get("guid") or "").strip()

        if not title or not company or not application_url:
            return None

        location = str(item.get("location") or item.get("jobLocation") or "Remote").strip()
        is_remote = "remote" in location.lower() or bool(item.get("isRemote", False))
        country = "India" if any(c in location.lower() for c in ["chennai", "bengaluru", "bangalore", "coimbatore", "india"]) else "Worldwide"

        return Job(
            external_id=external_id,
            title=title[:255],
            company=company[:255],
            description=description[:5000],
            location=location[:255],
            country=country,
            work_mode="remote" if is_remote else "onsite",
            source=self.name,
            application_url=application_url,
            source_url=application_url,
            posted_date=str(item.get("postedAt") or item.get("postedDate") or ""),
        )

    def fetch_jobs(self) -> list[Job]:
        if not self.api_key:
            self.last_status = "Not configured"
            logger.info("Source %s skipped: APIFY_API_KEY is not configured", self.name)
            return []

        jobs: list[Job] = []
        seen: set[str] = set()
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}

        # Query actor run or dataset items directly
        url = f"{APIFY_BASE_URL}/acts/{self.actor_id.replace('/', '~')}/run-sync-get-dataset-items"
        run_input = {
            "queries": list(self.queries),
            "maxResults": 20,
        }

        try:
            response = httpx.post(
                url,
                headers=headers,
                json=run_input,
                timeout=self.timeout,
            )
            if response.status_code == 401:
                self.last_status = "Unauthorized (Invalid Key)"
                self.last_error = "HTTP 401: Invalid APIFY_API_KEY"
                logger.warning("Apify API key is invalid (401)")
                return []

            response.raise_for_status()
            items = response.json()
            if not isinstance(items, list):
                items = items.get("items", []) if isinstance(items, dict) else []

            for item in items:
                if not isinstance(item, dict):
                    continue
                job = self._parse_item(item)
                if job and job.application_url not in seen:
                    seen.add(job.application_url)
                    jobs.append(job)

            self.last_status = "Connected"
            self.last_error = ""

        except Exception as exc:
            self.last_status = "Failed"
            self.last_error = str(exc)
            logger.warning("Apify source %s failed: %s", self.name, exc)

        return jobs
