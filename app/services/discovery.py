from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.parse import quote_plus

from sqlalchemy.orm import Session

from app.db.models import JobModel
from app.models.schemas import DiscoveryRunResult, Job
from app.services.deduplication import deduplicate_jobs
from app.services.llm import get_llm_provider
from app.services.normalization import normalize_job
from app.services.scoring import score_job
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
    """Build navigational search URLs; this does not scrape or bypass a site."""
    results: list[dict[str, str]] = []
    for source in SOURCES:
        for keyword in keywords:
            for location in locations:
                if not keyword.strip() or not location.strip():
                    continue
                results.append(
                    {
                        "source": source.name,
                        "keyword": keyword,
                        "location": location,
                        "url": source.url_template.format(
                            q=quote_plus(keyword.strip()), location=quote_plus(location.strip())
                        ),
                    }
                )
    return results


def _job_model_from_schema(job: Job, score_total: float, score_json: str, llm_json: str) -> JobModel:
    return JobModel(
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
        skills_json=json.dumps(job.skills),
        perks_json=json.dumps(job.perks),
        posted_date=job.posted_date,
        deadline=job.deadline,
        dedup_hash=job.dedup_hash,
        score_total=score_total,
        score_breakdown_json=score_json,
        llm_analysis_json=llm_json,
    )


def run_discovery_pipeline(db: Session) -> DiscoveryRunResult:
    """Run all configured adapters with source isolation and one DB transaction.

    A source may fail without preventing other sources from contributing. The
    database transaction is rolled back on persistence failure so a partial run
    cannot leave the session in a misleading state.
    """
    sources = get_default_sources()
    all_raw_jobs: list[Job] = []
    failed_sources = 0

    for source in sources:
        try:
            fetched = source.fetch_jobs()
            if not isinstance(fetched, list):
                raise TypeError("source returned a non-list result")
            valid = [job for job in fetched if isinstance(job, Job)]
            all_raw_jobs.extend(valid)
            logger.info("Discovery source %s returned %d jobs", source.name, len(valid))
        except Exception as exc:
            failed_sources += 1
            logger.exception("Discovery source %s failed: %s", source.name, exc)

    jobs_seen = len(all_raw_jobs)
    normalized = []
    for job in all_raw_jobs:
        try:
            normalized.append(normalize_job(job))
        except Exception as exc:
            logger.warning("Skipping malformed job from %s: %s", job.source, exc)

    existing_hashes = {row[0] for row in db.query(JobModel.dedup_hash).all() if row[0]}
    unique_jobs, duplicate_count = deduplicate_jobs(normalized, existing_hashes=existing_hashes)

    new_jobs = 0
    high_fit = 0
    llm = get_llm_provider()

    try:
        for job in unique_jobs:
            score = score_job(job)
            analysis = None
            if score.total >= 40.0:
                try:
                    analysis = llm.analyze_job_description(job)
                    job.llm_analysis = analysis
                except Exception as exc:
                    # The LLM is an enrichment layer, never a discovery dependency.
                    logger.warning("LLM enrichment failed for %s: %s", job.title, exc)

            db.add(
                _job_model_from_schema(
                    job,
                    score.total,
                    json.dumps(score.model_dump()),
                    json.dumps(analysis.model_dump()) if analysis else "{}",
                )
            )
            new_jobs += 1
            if score.total >= 70.0:
                high_fit += 1
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Discovery persistence transaction rolled back")
        raise

    return DiscoveryRunResult(
        sources_checked=len(sources),
        jobs_seen=jobs_seen,
        new_jobs=new_jobs,
        duplicates=duplicate_count,
        failed_sources=failed_sources,
        high_fit_jobs=high_fit,
    )
