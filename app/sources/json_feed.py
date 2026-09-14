from __future__ import annotations

import logging
import httpx
from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)


class JSONFeedJobSource(JobSource):
    def __init__(self, name: str, url: str, items_key: str | None = None):
        self.name = name
        self.url = url
        self.items_key = items_key

    def fetch_jobs(self) -> list[Job]:
        jobs: list[Job] = []
        try:
            headers = {"User-Agent": "AI-Internship-Agent/1.0", "Accept": "application/json"}
            response = httpx.get(self.url, headers=headers, timeout=10.0, follow_redirects=True)
            if response.status_code != 200:
                logger.warning(f"JSON Feed source {self.name} returned status code {response.status_code}")
                return jobs

            data = response.json()
            items = data
            if self.items_key and isinstance(data, dict):
                items = data.get(self.items_key, [])

            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    title = item.get("title") or item.get("role") or item.get("position") or "AI Intern"
                    company = item.get("company") or item.get("company_name") or "Tech Company"
                    description = item.get("description") or item.get("details") or ""
                    location = item.get("location") or item.get("city") or "Bengaluru"
                    work_mode = item.get("work_mode") or item.get("remote") or "remote"
                    app_url = item.get("url") or item.get("apply_url") or item.get("link") or ""
                    stipend = item.get("stipend") or item.get("stipend_monthly_inr")

                    try:
                        stipend_val = int(stipend) if stipend is not None else None
                    except (ValueError, TypeError):
                        stipend_val = None

                    jobs.append(
                        Job(
                            external_id=str(item.get("id", "")),
                            title=str(title),
                            company=str(company),
                            description=str(description),
                            location=str(location),
                            work_mode=str(work_mode),
                            stipend_monthly_inr=stipend_val,
                            source=self.name,
                            application_url=str(app_url),
                            source_url=str(app_url),
                        )
                    )
        except Exception as e:
            logger.error(f"Error fetching JSON Feed job source {self.name}: {e}")
        return jobs
