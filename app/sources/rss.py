from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)


class RSSJobSource(JobSource):
    """Read a public RSS/Atom feed without inventing missing job data."""

    def __init__(self, name: str, url: str, default_country: str = "Worldwide", timeout: float = 15.0):
        self.name = name
        self.url = url
        self.default_country = default_country
        self.timeout = timeout

    @staticmethod
    def _text(element: ET.Element | None) -> str:
        return "" if element is None or element.text is None else element.text.strip()

    def fetch_jobs(self) -> list[Job]:
        try:
            response = httpx.get(
                self.url,
                headers={"User-Agent": "AI-Internship-Agent/1.0", "Accept": "application/rss+xml, application/atom+xml, application/xml"},
                timeout=self.timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
            root = ET.fromstring(response.text)
        except (httpx.HTTPError, ET.ParseError) as exc:
            logger.warning("RSS source %s failed: %s", self.name, exc)
            return []

        atom = "{http://www.w3.org/2005/Atom}"
        items = root.findall(".//item") or root.findall(f".//{atom}entry")
        jobs: list[Job] = []

        for item in items:
            title_el = item.find("title") or item.find(f"{atom}title")
            link_el = item.find("link") or item.find(f"{atom}link")
            desc_el = item.find("description") or item.find(f"{atom}content") or item.find(f"{atom}summary")
            pub_el = item.find("pubDate") or item.find(f"{atom}published") or item.find(f"{atom}updated")
            id_el = item.find("guid") or item.find(f"{atom}id")

            raw_title = self._text(title_el)
            link = self._text(link_el)
            if not link and link_el is not None:
                link = link_el.attrib.get("href", "").strip()
            description = self._text(desc_el)
            posted = self._text(pub_el)
            external_id = self._text(id_el)

            if not raw_title or not link:
                # A listing without identity + an actionable URL cannot be safely persisted.
                continue

            title = raw_title
            company = ""
            for separator in (" at ", " - "):
                if separator in title:
                    title, company = (part.strip() for part in title.split(separator, 1))
                    break

            if not company:
                # Keep the company unknown instead of fabricating one.
                company = "Unknown"

            jobs.append(
                Job(
                    external_id=external_id,
                    title=title[:255],
                    company=company[:255],
                    description=description[:5000],
                    location="Remote",
                    country=self.default_country,
                    work_mode="remote",
                    source=self.name,
                    application_url=link,
                    source_url=link,
                    posted_date=posted,
                )
            )

        return jobs
