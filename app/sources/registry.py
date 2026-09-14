from __future__ import annotations

from app.sources.base import JobSource
from app.sources.rss import RSSJobSource
from app.sources.json_feed import JSONFeedJobSource
from app.sources.company_careers import CuratedCompanyCareersSource


def get_default_sources() -> list[JobSource]:
    return [
        CuratedCompanyCareersSource(name="Curated AI Careers"),
        RSSJobSource(
            name="RemoteOK AI Jobs RSS",
            url="https://remoteok.com/remote-ai-jobs.rss",
            default_country="Worldwide",
        ),
        RSSJobSource(
            name="WeWorkRemotely Dev RSS",
            url="https://weworkremotely.com/categories/remote-programming-jobs.rss",
            default_country="Worldwide",
        ),
    ]
