from __future__ import annotations

import re
from typing import Any, Dict, List
from app.services.scoring import load_profile

FIELD_PATTERNS = {
    "first_name": ["first name", "firstname", "given name", "fname"],
    "last_name": ["last name", "lastname", "surname", "family name", "lname"],
    "full_name": ["full name", "name", "candidate name", "your name"],
    "email": ["email", "e-mail", "email address"],
    "phone": ["phone", "mobile", "contact number", "telephone", "phone number"],
    "location": ["current city", "city", "location", "address", "current location"],
    "linkedin": ["linkedin", "linkedin profile", "linkedin url"],
    "github": ["github", "github profile", "github url"],
    "portfolio": ["portfolio", "website", "personal website"],
    "education": ["degree", "education", "university", "college", "major"],
    "graduation_year": ["graduation year", "year of graduation", "grad year", "batch"],
    "stipend_expectation": ["stipend", "salary expectation", "expected stipend", "compensation"],
}


def get_candidate_form_defaults() -> Dict[str, str]:
    profile = load_profile()
    cand = profile.get("candidate", {})

    return {
        "first_name": cand.get("name", "Ranjith S").split()[0],
        "last_name": cand.get("name", "Ranjith S").split()[-1] if len(cand.get("name", "Ranjith S").split()) > 1 else "",
        "full_name": cand.get("name", "Ranjith S"),
        "email": "ranjithvijai12345@gmail.com",
        "phone": "+91 9876543210",
        "location": cand.get("current_city", "Chennai, India"),
        "linkedin": "https://linkedin.com/in/ranjith-s",
        "github": "https://github.com/ranjiths112007",
        "portfolio": "https://github.com/ranjiths112007",
        "education": cand.get("education", "B.Sc. Artificial Intelligence & Machine Learning"),
        "graduation_year": str(cand.get("graduation_year", 2027)),
        "stipend_expectation": f"INR {profile.get('minimum_monthly_stipend_inr', 40000)}/month",
    }


def detect_form_fields_from_html(html_content: str) -> Dict[str, Any]:
    """Inspects HTML for form fields matching standard job application patterns."""
    html_lower = html_content.lower()
    detected = []
    missing = []

    for field, patterns in FIELD_PATTERNS.items():
        matched = any(p in html_lower for p in patterns)
        if matched:
            detected.append(field)
        else:
            missing.append(field)

    return {
        "detected_fields": detected,
        "missing_fields": missing,
        "mapped_values": get_candidate_form_defaults(),
    }
