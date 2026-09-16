from __future__ import annotations

from app.models.schemas import Job
from app.sources.apify import ApifyJobSource


def test_apify_source_unconfigured():
    source = ApifyJobSource(name="Test Apify Source")
    source.api_key = ""
    jobs = source.fetch_jobs()
    assert jobs == []
    assert source.last_status == "Not configured"


def test_apify_item_parsing():
    source = ApifyJobSource(name="Test Apify Source")
    item = {
        "title": "AI Research Intern",
        "company": "DeepMind",
        "url": "https://example.com/job/123",
        "location": "Bengaluru, India",
        "description": "Building next-gen AI models using PyTorch.",
    }
    parsed = source._parse_item(item)
    assert isinstance(parsed, Job)
    assert parsed.title == "AI Research Intern"
    assert parsed.company == "DeepMind"
    assert parsed.country == "India"
