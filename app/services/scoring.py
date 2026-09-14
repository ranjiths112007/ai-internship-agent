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
    all_text = _norm(" ".join([job.title, job.description, *job.skills, job.location]))

    reasons: list[str] = []
    flags: list[str] = []

    # 1. Seniority & Hard Eligibility Check
    is_senior = any(k in all_text for k in ["3+ years", "5+ years", "senior engineer", "lead engineer", "principal engineer", "staff engineer"])
    is_intern = any(k in all_text for k in ["intern", "internship", "trainee", "fresher", "co-op", "graduate intern"])

    seniority_penalty = 0.0
    if is_senior and not is_intern:
        seniority_penalty = 40.0
        flags.append("Role requires senior-level (3+ years) experience; intern candidate penalty applied.")

    # 2. Role Relevance
    target_roles = profile.get("target_roles", [])
    exact_role_hit = any(_contains(title_text, role) for role in target_roles)

    role_keywords = [
        "ai engineer", "genai", "generative ai", "applied ai", "machine learning",
        "ml engineer", "ai/ml", "llm", "rag", "ai agent", "artificial intelligence",
        "software engineer", "backend engineer"
    ]
    role_hits = sum(1 for keyword in role_keywords if _contains(title_text, keyword))

    if exact_role_hit:
        role_relevance = 100.0
        reasons.append("Exact match with target AI/ML engineering role titles.")
    elif role_hits > 0:
        role_relevance = min(100.0, 50.0 + role_hits * 15.0)
        reasons.append("Title strongly aligns with target AI/ML keywords.")
    else:
        role_relevance = 25.0
        flags.append("Title does not closely match primary AI/ML target roles.")

    role_relevance = max(0.0, role_relevance - seniority_penalty)

    # 3. Skill Overlap & Project Evidence Match
    profile_skills = profile.get("skills", [])
    matched_skills = [skill for skill in profile_skills if _contains(all_text, skill)]

    # Project evidence alignment
    evidence_hits = 0
    if _contains(all_text, "rag") or _contains(all_text, "pgvector") or _contains(all_text, "embeddings"):
        evidence_hits += 1
        reasons.append("Matches candidate evidence in RAG & pgvector vector search.")
    if _contains(all_text, "agent") or _contains(all_text, "tool calling"):
        evidence_hits += 1
        reasons.append("Matches candidate evidence in AI Agent building & Tool Calling.")
    if _contains(all_text, "ocr") or _contains(all_text, "tesseract") or _contains(all_text, "opencv"):
        evidence_hits += 1
        reasons.append("Matches candidate evidence in OpenCV / OCR document pipelines.")

    skill_match = min(100.0, (len(matched_skills) / 4.0) * 60.0 + evidence_hits * 15.0)

    if matched_skills:
        reasons.append(f"Matches {len(matched_skills)} candidate skills: {', '.join(matched_skills[:8])}.")
    else:
        flags.append("No direct candidate skill overlap found in available text.")

    # 4. Location & Remote Lane Match
    location_text = _norm(job.location + " " + job.country)
    preferred_locations = [_norm(x) for x in profile.get("locations", [])]

    is_remote = "remote" in location_text or "remote" in _norm(job.work_mode) or "wfh" in location_text
    location_hit = any(loc in location_text for loc in preferred_locations)
    intl_remote = profile.get("international_remote", True) and is_remote

    if location_hit:
        location_match = 100.0
        reasons.append("Location matches a target Indian city (Chennai, Bengaluru, Coimbatore).")
    elif intl_remote and ("worldwide" in location_text or "global" in location_text or "unrestricted" in location_text or "india" in location_text or job.location_category == "international_remote"):
        location_match = 100.0
        reasons.append("Eligible for the International Remote lane.")
    elif is_remote:
        location_match = 75.0
        reasons.append("Remote position available.")
        if "us only" in location_text or "us remote" in location_text:
            flags.append("Location notes US-only remote constraint; work authorization check recommended.")
    else:
        location_match = 25.0
        flags.append(f"Location '{job.location}' is outside target Indian cities without explicit remote work.")

    # 5. Compensation Match
    stipend = job.stipend_monthly_inr
    minimum = profile.get("minimum_monthly_stipend_inr", 40000)

    if stipend is None:
        compensation = 45.0
        flags.append("Compensation undisclosed; manual verification recommended.")
    elif stipend >= minimum:
        compensation = 100.0
        reasons.append(f"Stipend (INR {stipend:,}/month) meets or exceeds the INR {minimum:,}/month target.")
    else:
        compensation = max(20.0, (stipend / minimum) * 100.0)
        flags.append(f"Stipend (INR {stipend:,}/month) is below the INR {minimum:,}/month target.")

    # 6. Work Mode Match
    preferred_modes = [_norm(x) for x in profile.get("work_modes", ["onsite", "remote"])]
    work_mode_val = _norm(job.work_mode)
    if work_mode_val in preferred_modes or (is_remote and "remote" in preferred_modes):
        work_mode = 100.0
    else:
        work_mode = 40.0

    # 7. Company Signal Match
    company_text = _norm(job.company + " " + job.description)
    company_signals = ["startup", "product", "venture", "funded", "technology", "saas", "labs", "ai", "tech"]
    signal_hits = sum(1 for x in company_signals if x in company_text)
    company_signal = min(100.0, 40.0 + signal_hits * 10.0)

    if signal_hits >= 2:
        reasons.append("Company exhibits positive startup/product engineering signals.")

    # Final Total Weight Calculation
    total = round(
        role_relevance * 0.25
        + skill_match * 0.30
        + location_match * 0.10
        + compensation * 0.15
        + work_mode * 0.05
        + company_signal * 0.15,
        2,
    )
    total = min(100.0, max(0.0, total))

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
