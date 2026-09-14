from __future__ import annotations

import re
from app.models.schemas import Job


def normalize_title(title: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def classify_location_and_remote(location: str, country: str, work_mode: str) -> tuple[str, str]:
    """
    Returns (remote_category, location_category)
    remote_category options:
      'india_remote', 'worldwide_remote', 'apac_remote', 'us_only', 'europe_remote', 'unrestricted_remote', 'onsite', 'hybrid', 'unknown'
    location_category options:
      'india', 'international_remote', 'international_hybrid', 'international_onsite', 'unknown'
    """
    loc_lower = location.lower().strip()
    country_lower = country.lower().strip()
    mode_lower = work_mode.lower().strip()

    is_remote = "remote" in loc_lower or "wfh" in loc_lower or "work from home" in loc_lower or "remote" in mode_lower

    if is_remote:
        if "india" in loc_lower or "in only" in loc_lower or "india only" in loc_lower:
            remote_cat = "india_remote"
            loc_cat = "india"
        elif "us" in loc_lower or "united states" in loc_lower or "us only" in loc_lower:
            remote_cat = "us_only"
            loc_cat = "international_remote"
        elif "europe" in loc_lower or "eu" in loc_lower:
            remote_cat = "europe_remote"
            loc_cat = "international_remote"
        elif "apac" in loc_lower:
            remote_cat = "apac_remote"
            loc_cat = "international_remote"
        elif "worldwide" in loc_lower or "global" in loc_lower or "unrestricted" in loc_lower or "anywhere" in loc_lower:
            remote_cat = "worldwide_remote"
            loc_cat = "international_remote"
        else:
            if country_lower in ["india", "in"]:
                remote_cat = "india_remote"
                loc_cat = "india"
            else:
                remote_cat = "worldwide_remote"
                loc_cat = "international_remote"
    else:
        if "hybrid" in mode_lower or "hybrid" in loc_lower:
            if any(c in loc_lower for c in ["chennai", "bengaluru", "bangalore", "coimbatore", "india"]):
                remote_cat = "hybrid"
                loc_cat = "india"
            else:
                remote_cat = "hybrid"
                loc_cat = "international_hybrid"
        else:
            if any(c in loc_lower for c in ["chennai", "bengaluru", "bangalore", "coimbatore", "india"]) or country_lower in ["india", "in"]:
                remote_cat = "onsite"
                loc_cat = "india"
            else:
                remote_cat = "onsite"
                loc_cat = "international_onsite"

    return remote_cat, loc_cat


def normalize_stipend_to_inr(stipend: int | float | None, currency: str = "INR") -> int | None:
    if stipend is None:
        return None

    curr_upper = currency.upper().strip()
    # Live or standard conversion rates for normalization
    rates = {
        "INR": 1.0,
        "USD": 83.5,
        "EUR": 90.0,
        "GBP": 105.0,
        "SGD": 62.0,
        "CAD": 61.0,
        "AUD": 55.0,
    }
    rate = rates.get(curr_upper, 1.0)
    return int(stipend * rate)


def normalize_job(job: Job) -> Job:
    """Modifies job in-place with normalized values."""
    job.normalized_title = normalize_title(job.title)
    rem_cat, loc_cat = classify_location_and_remote(job.location, job.country, job.work_mode)
    job.remote_category = rem_cat
    job.location_category = loc_cat

    if job.stipend_monthly_inr is None and job.salary_text:
        # Try extracting numbers from salary_text
        match = re.search(r"(\d[\d,]*)\s*(k|thousand)?", job.salary_text.lower())
        if match:
            num_str = match.group(1).replace(",", "")
            try:
                val = int(num_str)
                if match.group(2):
                    val *= 1000
                job.stipend_monthly_inr = normalize_stipend_to_inr(val, job.currency)
            except ValueError:
                pass
    elif job.stipend_monthly_inr is not None and job.currency != "INR":
        job.stipend_monthly_inr = normalize_stipend_to_inr(job.stipend_monthly_inr, job.currency)

    return job
