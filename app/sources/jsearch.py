from __future__ import annotations

import logging
import httpx
from app.core.config import settings
from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)


class JSearchJobSource(JobSource):
    """
    Job source adapter for OpenWebNinja JSearch API (api.openwebninja.com/jsearch/search-v2).
    Fetches real live job listings for AI/ML engineering internships.
    """

    def __init__(self, name: str = "JSearch API (OpenWebNinja)", api_key: str | None = None):
        self.name = name
        self.api_key = api_key or settings.openwebninja_api_key

    def fetch_jobs(self) -> list[Job]:
        jobs: list[Job] = []
        if not self.api_key:
            logger.info(f"Source {self.name}: OPENWEBNINJA_API_KEY is not configured. Skipping live API fetch.")
            return jobs

        queries = [
            "AI Engineer intern in India",
            "Generative AI intern",
            "Machine Learning Engineer intern in Bengaluru",
        ]

        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }

        for query in queries:
            try:
                params = {"query": query, "num_pages": 1}
                resp = httpx.get(
                    "https://api.openwebninja.com/jsearch/search-v2",
                    headers=headers,
                    params=params,
                    timeout=20.0,
                )
                if resp.status_code != 200:
                    logger.warning(f"JSearch API returned status code {resp.status_code} for query '{query}'")
                    continue

                data = resp.json()
                items = data.get("data", []) if isinstance(data, dict) else []

                for item in items:
                    if not isinstance(item, dict):
                        continue

                    title = item.get("job_title") or "AI Intern"
                    company = item.get("employer_name") or "Tech Company"
                    description = item.get("job_description") or ""

                    city = item.get("job_city") or ""
                    state = item.get("job_state") or ""
                    country = item.get("job_country") or "India"

                    loc_parts = [p for p in [city, state, country] if p]
                    location_str = ", ".join(loc_parts) if loc_parts else "India"

                    is_remote = item.get("job_is_remote", False)
                    work_mode = "remote" if is_remote else "onsite"

                    min_sal = item.get("job_min_salary")
                    max_sal = item.get("job_max_salary")
                    salary_period = item.get("job_salary_period", "").lower()

                    stipend_monthly = None
                    if min_sal or max_sal:
                        sal_val = max_sal or min_sal
                        if "year" in salary_period:
                            stipend_monthly = int(sal_val / 12)
                        elif "month" in salary_period:
                            stipend_monthly = int(sal_val)

                    app_url = item.get("job_apply_link") or item.get("job_google_link") or ""

                    jobs.append(
                        Job(
                            external_id=str(item.get("job_id", "")),
                            title=str(title),
                            company=str(company),
                            description=str(description[:3000]),
                            location=location_str,
                            country=str(country),
                            work_mode=work_mode,
                            stipend_monthly_inr=stipend_monthly,
                            salary_text=f"{min_sal}-{max_sal} {salary_period}" if min_sal else "",
                            source=self.name,
                            application_url=str(app_url),
                            source_url=str(app_url),
                            posted_date=str(item.get("job_posted_at_datetime_utc", "")),
                        )
                    )
            except Exception as e:
                logger.error(f"Error fetching from JSearch API for query '{query}': {e}")

        return jobs
