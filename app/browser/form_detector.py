from __future__ import annotations

import re
from typing import Any, Dict

from app.services.scoring import load_profile

FIELD_PATTERNS = {
    "first_name": ["first name", "firstname", "given name", "fname"],
    "last_name": ["last name", "lastname", "surname", "family name", "lname"],
    "full_name": ["full name", "candidate name", "your name"],
    "email": ["email", "e-mail", "email address"],
    "phone": ["phone", "mobile", "contact number", "telephone", "phone number"],
    "location": ["current city", "city", "location", "current location"],
    "linkedin": ["linkedin", "linkedin profile", "linkedin url"],
    "github": ["github", "github profile", "github url"],
    "portfolio": ["portfolio", "website", "personal website"],
    "education": ["degree", "education", "university", "college", "major"],
    "graduation_year": ["graduation year", "year of graduation", "grad year", "batch"],
    "stipend_expectation": ["stipend", "salary expectation", "expected stipend", "compensation"],
}


def _profile_contact(profile: dict, key: str) -> str:
    """Read optional contact data without inventing personal information."""
    contacts = profile.get("contact", {})
    if isinstance(contacts, dict):
        value = contacts.get(key, "")
        return str(value).strip() if value is not None else ""
    return ""


def get_candidate_form_defaults() -> Dict[str, str]:
    profile = load_profile()
    cand = profile.get("candidate", {})
    name = str(cand.get("name", "")).strip()
    parts = name.split()
    minimum = profile.get("minimum_monthly_stipend_inr")

    return {
        "first_name": parts[0] if parts else "",
        "last_name": " ".join(parts[1:]) if len(parts) > 1 else "",
        "full_name": name,
        "email": _profile_contact(profile, "email"),
        "phone": _profile_contact(profile, "phone"),
        "location": str(cand.get("current_city", "")).strip(),
        "linkedin": _profile_contact(profile, "linkedin"),
        "github": _profile_contact(profile, "github"),
        "portfolio": _profile_contact(profile, "portfolio"),
        "education": str(cand.get("education", "")).strip(),
        "graduation_year": str(cand.get("graduation_year", "")),
        "stipend_expectation": f"INR {minimum}/month" if minimum else "",
    }


def detect_form_fields_from_html(html_content: str) -> Dict[str, Any]:
    """Inspect HTML for likely application fields.

    This is intentionally conservative: detection only reports likely fields;
    it does not authorize filling sensitive fields or submitting a form.
    """
    html_lower = re.sub(r"\s+", " ", str(html_content or "").lower())
    detected: list[str] = []
    missing: list[str] = []

    for field, patterns in FIELD_PATTERNS.items():
        (detected if any(p in html_lower for p in patterns) else missing).append(field)

    return {
        "detected_fields": detected,
        "missing_fields": missing,
        "mapped_values": get_candidate_form_defaults(),
        "sensitive_fields": ["phone", "location", "stipend_expectation"],
        "requires_manual_review": True,
    }
