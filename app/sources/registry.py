from __future__ import annotations

from app.services.scoring import load_profile
from app.sources.base import JobSource
from app.sources.jsearch import JSearchJobSource
from app.sources.rss import RSSJobSource


def get_default_sources() -> list[JobSource]:
    """Return only real external sources, with searches derived from the candidate profile."""
    profile = load_profile()
    roles = profile.get("target_roles", [])[:6]
    locations = profile.get("locations", [])[:4]
    queries: list[str] = []
    for role in roles:
        for location in locations:
            queries.append(f'"{role}" internship {location}')
    queries.extend(["AI Engineer internship remote", "Generative AI internship remote"])
    # Keep API usage bounded while still covering the candidate's actual lanes.
    unique_queries = tuple(dict.fromkeys(queries))[:12]

    return [
        JSearchJobSource(name="JSearch API (OpenWebNinja)", queries=unique_queries),
        RSSJobSource(name="RemoteOK AI Jobs RSS", url="https://remoteok.com/remote-ai-jobs.rss", default_country="Worldwide"),
        RSSJobSource(name="WeWorkRemotely Programming RSS", url="https://weworkremotely.com/categories/remote-programming-jobs.rss", default_country="Worldwide"),
    ]
