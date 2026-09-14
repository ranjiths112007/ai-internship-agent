from __future__ import annotations

import json
import re
from pathlib import Path

from app.models.schemas import Job, ScoreBreakdown

PROFILE_PATH = Path(__file__).resolve().parents[2] / "config" / "candidate_profile.json"


def load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().strip())


def _contains(text: str, term: str) -> bool:
    text = _norm(text)
    term = _norm(term)
    return term in text


def score_job(job: Job) -> ScoreBreakdown:
    profile = load_profile()
    title_text = _norm(job.title)
    all_text = _norm(" ".join([job.title, job.description, *job.skills]))

    role_keywords = [
        "ai engineer", "genai", "generative ai", "applied ai", "machine learning",
        "ml engineer", "ai/ml", "llm", "rag", "ai agent", "artificial intelligence",
        "software engineer", "backend engineer"
    ]
    role_hits = sum(1 for keyword in role_keywords if _contains(title_text, keyword))
    role_relevance = min(100.0, 50.0 + role_hits * 12.5) if role_hits else 20.0

    profile_skills = profile["skills"]
    matched = [skill for skill in profile_skills if _contains(all_text, skill)]
    skill_match = min(100.0, (len(matched) / max(1, min(12, len(profile_skills)))) * 100)

    location_text = _norm(job.location)
    preferred_locations = [_norm(x) for x in profile["locations"]]
    remote = _contains(job.work_mode, "remote")
    location_hit = any(loc in location_text for loc in preferred_locations)
    international_remote = profile["international_remote"] and remote
    location_match = 100.0 if location_hit or international_remote else 25.0

    stipend = job.stipend_monthly_inr
    minimum = profile["minimum_monthly_stipend_inr"]
    if stipend is None:
        compensation = 45.0
    elif stipend >= minimum:
        compensation = 100.0
    else:
        compensation = max(20.0, (stipend / minimum) * 100.0)

    preferred_modes = [_norm(x) for x in profile["work_modes"]]
    work_mode = 100.0 if _norm(job.work_mode) in preferred_modes else 30.0

    company_text = _norm(job.company + " " + job.description)
    company_signals = ["startup", "product", "venture", "funded", "technology", "saas"]
    signal_hits = sum(1 for x in company_signals if x in company_text)
    company_signal = min(100.0, 40.0 + signal_hits * 10.0)

    total = round(
        role_relevance * 0.25
        + skill_match * 0.30
        + location_match * 0.10
        + compensation * 0.15
        + work_mode * 0.05
        + company_signal * 0.15,
        2,
    )

    reasons: list[str] = []
    flags: list[str] = []
    if matched:
        reasons.append(f"Matches {len(matched)} profile skills: {', '.join(matched[:8])}.")
    if role_relevance >= 75:
        reasons.append("Role title is strongly aligned with the AI/ML target.")
    if location_hit:
        reasons.append("Location matches a preferred Indian city.")
    elif international_remote:
        reasons.append("Remote opportunity is eligible for the international lane.")
    if stipend is not None and stipend >= minimum:
        reasons.append(f"Stipend meets the INR {minimum:,}/month target.")
    elif stipend is None:
        flags.append("Compensation not disclosed; manual verification recommended.")
    else:
        flags.append(f"Stipend is below the INR {minimum:,}/month target.")
    if not matched:
        flags.append("No strong resume-skill overlap found from available JD text.")

    return ScoreBreakdown(
        role_relevance=round(role_relevance, 2),
        skill_match=round(skill_match, 2),
        location_match=round(location_match, 2),
        compensation=round(compensation, 2),
        work_mode=round(work_mode, 2),
        company_signal=round(company_signal, 2),
        total=total,
        reasons=reasons,
        flags=flags,
    )
