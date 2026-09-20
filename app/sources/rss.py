from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)


def _first_present(item: ET.Element, *tags: str) -> ET.Element | None:
    """Return the first matching child element, checked by identity (`is not None`).

    `ET.Element.__bool__` is based on child count, not on whether the element
    has text -- a plain leaf element like `<title>Some text</title>` is falsy
    because it has zero *child elements*. Chaining `item.find(a) or item.find(b)`
    therefore silently discards a perfectly valid match whenever it has no
    children (i.e. for almost every RSS/Atom leaf field), making the source
    treat present data as missing. This helper checks presence explicitly.
    """
    for tag in tags:
        element = item.find(tag)
        if element is not None:
            return element
    return None


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
            title_el = _first_present(item, "title", f"{atom}title")
            link_el = _first_present(item, "link", f"{atom}link")
            desc_el = _first_present(item, "description", f"{atom}content", f"{atom}summary")
            pub_el = _first_present(item, "pubDate", f"{atom}published", f"{atom}updated")
            id_el = _first_present(item, "guid", f"{atom}id")

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
