from __future__ import annotations

import hashlib
from urllib.parse import urlparse
from app.models.schemas import Job
from app.services.normalization import normalize_title


def compute_dedup_hash(job: Job) -> str:
    """
    Computes a deterministic hash using multi-signal strategy:
    1. source + external_id (if external_id exists)
    2. clean application_url
    3. company + normalized_title + location
    """
    if job.source and job.external_id:
        seed = f"id:{job.source.strip().lower()}:{job.external_id.strip().lower()}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    if job.application_url:
        parsed = urlparse(job.application_url.strip().lower())
        clean_url = f"{parsed.netloc}{parsed.path}"
        if len(clean_url) > 10:
            seed = f"url:{clean_url}"
            return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    norm_title = normalize_title(job.title)
    norm_company = job.company.strip().lower()
    norm_loc = job.location.strip().lower()
    seed = f"meta:{norm_company}:{norm_title}:{norm_loc}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def deduplicate_jobs(jobs: list[Job], existing_hashes: set[str] | None = None) -> tuple[list[Job], int]:
    """
    Deduplicates a list of jobs against themselves and optionally against existing DB hashes.
    Returns (unique_jobs, duplicate_count).
    """
    seen_hashes: set[str] = set(existing_hashes) if existing_hashes else set()
    unique_jobs: list[Job] = []
    duplicate_count = 0

    for job in jobs:
        d_hash = compute_dedup_hash(job)
        job.dedup_hash = d_hash
        if d_hash in seen_hashes:
            duplicate_count += 1
        else:
            seen_hashes.add(d_hash)
            unique_jobs.append(job)

    return unique_jobs, duplicate_count
