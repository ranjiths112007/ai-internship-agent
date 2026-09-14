from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus
from sqlalchemy.orm import Session

from app.db.models import JobModel
from app.models.schemas import DiscoveryRunResult, Job
from app.services.deduplication import compute_dedup_hash, deduplicate_jobs
from app.services.llm import get_llm_provider
from app.services.normalization import normalize_job
from app.services.scoring import load_profile, score_job
from app.sources.registry import get_default_sources

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchSource:
    name: str
    url_template: str


SOURCES = [
    SearchSource("LinkedIn", "https://www.linkedin.com/jobs/search/?keywords={q}&location={location}"),
    SearchSource("Indeed", "https://www.indeed.com/jobs?q={q}&l={location}"),
    SearchSource("Wellfound", "https://wellfound.com/jobs"),
    SearchSource("Internshala", "https://internshala.com/internships/"),
]


def build_search_urls(keywords: list[str], locations: list[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for source in SOURCES:
        for keyword in keywords:
            for location in locations:
                results.append(
                    {
                        "source": source.name,
                        "keyword": keyword,
                        "location": location,
                        "url": source.url_template.format(
                            q=quote_plus(keyword), location=quote_plus(location)
                        ),
                    }
                )
    return results


def run_discovery_pipeline(db: Session) -> DiscoveryRunResult:
    sources = get_default_sources()
    sources_checked = len(sources)
    failed_sources = 0

    all_raw_jobs: list[Job] = []
    for source in sources:
        try:
            fetched = source.fetch_jobs()
            all_raw_jobs.extend(fetched)
        except Exception as e:
            logger.error(f"Source {source.name} failed during discovery: {e}")
            failed_sources += 1

    jobs_seen = len(all_raw_jobs)

    # 1. Normalize
    normalized_list = [normalize_job(j) for j in all_raw_jobs]

    # 2. Get existing dedup hashes from DB
    existing_hashes = set(row[0] for row in db.query(JobModel.dedup_hash).all() if row[0])

    # 3. Deduplicate
    unique_jobs, dup_count = deduplicate_jobs(normalized_list, existing_hashes=existing_hashes)

    new_jobs_count = 0
    high_fit_count = 0

    llm = get_llm_provider()

    # 4. Score, Analyze, and Persist
    for job in unique_jobs:
        score_breakdown = score_job(job)

        # Run LLM / Fallback analysis for relevant jobs
        if score_breakdown.total >= 40.0:
            analysis = llm.analyze_job_description(job)
            job.llm_analysis = analysis

        score_json = json.dumps(score_breakdown.model_dump())
        llm_json = json.dumps(job.llm_analysis.model_dump()) if job.llm_analysis else "{}"
        skills_json = json.dumps(job.skills)
        perks_json = json.dumps(job.perks)

        job_model = JobModel(
            external_id=job.external_id,
            source=job.source,
            title=job.title,
            normalized_title=job.normalized_title,
            company=job.company,
            description=job.description,
            location=job.location,
            country=job.country,
            work_mode=job.work_mode,
            remote_category=job.remote_category,
            location_category=job.location_category,
            employment_type=job.employment_type,
            stipend_monthly_inr=job.stipend_monthly_inr,
            salary_text=job.salary_text,
            currency=job.currency,
            application_url=job.application_url,
            source_url=job.source_url,
            skills_json=skills_json,
            perks_json=perks_json,
            posted_date=job.posted_date,
            deadline=job.deadline,
            dedup_hash=job.dedup_hash,
            score_total=score_breakdown.total,
            score_breakdown_json=score_json,
            llm_analysis_json=llm_json,
        )
        db.add(job_model)
        new_jobs_count += 1
        if score_breakdown.total >= 70.0:
            high_fit_count += 1

    db.commit()

    return DiscoveryRunResult(
        sources_checked=sources_checked,
        jobs_seen=jobs_seen,
        new_jobs=new_jobs_count,
        duplicates=dup_count,
        failed_sources=failed_sources,
        high_fit_jobs=high_fit_count,
    )
