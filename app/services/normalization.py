from __future__ import annotations

import re
from app.models.schemas import Job


INDIA_CITIES = {
    "chennai": "Chennai",
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "coimbatore": "Coimbatore",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "mumbai": "Mumbai",
    "delhi": "Delhi",
    "new delhi": "Delhi",
}

COMMON_SKILLS = (
    "python", "fastapi", "flask", "django", "sql", "postgresql", "mysql", "mongodb",
    "docker", "kubernetes", "git", "github actions", "pytest", "pandas", "numpy",
    "scikit-learn", "scikit learn", "tensorflow", "pytorch", "opencv", "tesseract",
    "llm", "llms", "rag", "retrieval augmented generation", "embeddings", "vector search",
    "pgvector", "sentence transformers", "transformers", "prompt engineering", "ai agents",
    "tool calling", "openai", "gemini", "generative ai", "machine learning", "deep learning",
    "typescript", "react", "next.js", "rest api", "rest apis", "sqlalchemy",
)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).strip()


def normalize_title(title: str) -> str:
    cleaned = re.sub(r"[^\w\s+#.-]", " ", (title or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def classify_location_and_remote(location: str, country: str, work_mode: str) -> tuple[str, str]:
    """Return conservative remote/location classifications.

    Unknown remote scope stays unknown rather than being upgraded to worldwide.
    This prevents a generic 'remote' listing from being incorrectly presented as
    international-remote eligible.
    """
    loc = _clean(location).lower()
    ctr = _clean(country).lower()
    mode = _clean(work_mode).lower()
    combined = f"{loc} {ctr} {mode}"

    is_hybrid = "hybrid" in combined
    is_remote = any(x in combined for x in ("remote", "wfh", "work from home", "work-from-home"))
    india = ctr in {"india", "in"} or "india" in loc or any(city in loc for city in INDIA_CITIES)

    if is_remote:
        if "india only" in combined or "india" in loc or ctr in {"india", "in"}:
            return "india_remote", "india"
        if any(x in combined for x in ("worldwide", "global remote", "global", "anywhere", "unrestricted", "work from anywhere")):
            return "worldwide_remote", "international_remote"
        if "apac" in combined or "asia pacific" in combined:
            return "apac_remote", "international_remote"
        if "europe" in combined or "european union" in combined:
            return "europe_remote", "international_remote"
        if re.search(r"\b(us|usa|united states)\b", combined) or "us only" in combined:
            return "us_only", "international_remote"
        return "unknown", "unknown"

    if is_hybrid:
        return "hybrid", "india" if india else "international_hybrid"

    if india:
        return "onsite", "india"
    if ctr and ctr not in {"unknown", "n/a", "na"}:
        return "onsite", "international_onsite"
    return "unknown", "unknown"


def extract_skills(text: str, existing: list[str] | None = None) -> list[str]:
    """Extract a bounded, deterministic skill list from job text."""
    source = (text or "").lower()
    found: list[str] = []
    for skill in COMMON_SKILLS:
        pattern = re.escape(skill.lower()).replace(r"\ ", r"\s+")
        if re.search(rf"(?<![\w]){pattern}(?![\w])", source):
            canonical = "scikit-learn" if skill == "scikit learn" else skill
            if canonical not in found:
                found.append(canonical)
    for skill in existing or []:
        value = _clean(str(skill))
        if value and value.lower() not in {x.lower() for x in found}:
            found.append(value)
    return found[:50]


def parse_monthly_amount(text: str) -> float | None:
    """Extract a plausible monthly INR amount from salary text only when the text says monthly."""
    value = (text or "").lower().replace(",", "")
    matches = re.findall(r"(?:inr|rs\.?|₹)?\s*(\d+(?:\.\d+)?)\s*(k|thousand)?", value)
    if not matches:
        return None
    number, suffix = matches[0]
    amount = float(number) * (1000 if suffix else 1)
    if any(term in value for term in ("per month", "/month", "monthly", "month")):
        return amount
    return None


def normalize_stipend_to_inr(stipend: int | float | None, currency: str = "INR") -> int | None:
    """Normalize only currencies for which an explicit static rate is configured.

    Unknown/non-INR currencies return None because silently treating foreign money
    as INR would corrupt the candidate's compensation filter.
    """
    if stipend is None:
        return None
    try:
        amount = float(stipend)
    except (TypeError, ValueError):
        return None
    if amount < 0:
        return None
    currency = (currency or "INR").upper().strip()
    rates = {"INR": 1.0}
    rate = rates.get(currency)
    return int(amount * rate) if rate is not None else None


def normalize_job(job: Job) -> Job:
    """Normalize a job in-place while preserving source currency semantics."""
    job.title = _clean(job.title)[:255]
    job.company = _clean(job.company)[:255]
    job.location = _clean(job.location)[:255]
    job.country = _clean(job.country)[:100] or "Unknown"
    job.work_mode = _clean(job.work_mode).lower() or "unknown"
    job.currency = (_clean(job.currency).upper() or "INR")[:10]
    job.normalized_title = normalize_title(job.title)

    job.remote_category, job.location_category = classify_location_and_remote(
        job.location, job.country, job.work_mode
    )

    combined = " ".join([job.title, job.description, job.location, *job.skills])
    job.skills = extract_skills(combined, job.skills)

    if job.stipend_monthly_inr is None:
        parsed = parse_monthly_amount(job.salary_text)
        if parsed is not None and job.currency == "INR":
            job.stipend_monthly_inr = int(parsed)
    elif job.currency != "INR":
        # The field is explicitly INR. Do not invent FX rates.
        job.stipend_monthly_inr = None

    return job
