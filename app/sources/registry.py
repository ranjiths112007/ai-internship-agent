from __future__ import annotations

from app.services.resume import get_profile_dict
from app.sources.apify import ApifyJobSource
from app.sources.base import JobSource
from app.sources.jsearch import JSearchJobSource
from app.sources.rss import RSSJobSource


def get_default_sources() -> list[JobSource]:
    """Return configured real external job discovery adapters."""
    profile = get_profile_dict()
    target_roles = profile.get("target_roles", ["AI Engineer Intern", "Generative AI Intern"])[:4]
    locations = profile.get("locations", ["Bengaluru", "Chennai"])[:3]

    queries: list[str] = []
    for role in target_roles:
        for location in locations:
            queries.append(f"{role} in {location}")
        queries.append(f"{role} remote")

    unique_queries = tuple(dict.fromkeys(queries))[:8]

    return [
        ApifyJobSource(
            name="Apify Jobs Scraper",
            queries=unique_queries,
        ),
        JSearchJobSource(
            name="JSearch API (OpenWebNinja)",
            queries=unique_queries,
        ),
        RSSJobSource(
            name="WeWorkRemotely Programming RSS",
            url="https://weworkremotely.com/categories/remote-programming-jobs.rss",
            default_country="Worldwide",
        ),
        RSSJobSource(
            name="Remotive Remote Jobs RSS",
            url="https://remotive.com/remote-jobs/feed",
            default_country="Worldwide",
        ),
    ]
