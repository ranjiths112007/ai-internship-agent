from __future__ import annotations

from app.sources.base import JobSource
from app.sources.jsearch import JSearchJobSource
from app.sources.rss import RSSJobSource


def get_default_sources() -> list[JobSource]:
    """Return only sources intended for real discovery.

    Illustrative/curated sample listings are deliberately excluded from the
    production registry. Test fixtures should be injected by tests instead.
    """
    return [
        JSearchJobSource(name="JSearch API (OpenWebNinja)"),
        RSSJobSource(
            name="RemoteOK AI Jobs RSS",
            url="https://remoteok.com/remote-ai-jobs.rss",
            default_country="Worldwide",
        ),
        RSSJobSource(
            name="WeWorkRemotely Programming RSS",
            url="https://weworkremotely.com/categories/remote-programming-jobs.rss",
            default_country="Worldwide",
        ),
    ]
