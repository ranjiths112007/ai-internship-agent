from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
import httpx
from app.models.schemas import Job
from app.sources.base import JobSource

logger = logging.getLogger(__name__)


class RSSJobSource(JobSource):
    def __init__(self, name: str, url: str, default_country: str = "India"):
        self.name = name
        self.url = url
        self.default_country = default_country

    def fetch_jobs(self) -> list[Job]:
        jobs: list[Job] = []
        try:
            headers = {"User-Agent": "AI-Internship-Agent/1.0"}
            response = httpx.get(self.url, headers=headers, timeout=10.0, follow_redirects=True)
            if response.status_code != 200:
                logger.warning(f"RSS source {self.name} returned status code {response.status_code}")
                return jobs

            root = ET.fromstring(response.text)
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items:
                title_elem = item.find("title")
                if title_elem is None:
                    title_elem = item.find("{http://www.w3.org/2005/Atom}title")

                link_elem = item.find("link")
                if link_elem is None:
                    link_elem = item.find("{http://www.w3.org/2005/Atom}link")

                desc_elem = item.find("description")
                if desc_elem is None:
                    desc_elem = item.find("{http://www.w3.org/2005/Atom}content")
                if desc_elem is None:
                    desc_elem = item.find("{http://www.w3.org/2005/Atom}summary")

                pub_elem = item.find("pubDate")
                if pub_elem is None:
                    pub_elem = item.find("{http://www.w3.org/2005/Atom}published")

                title = title_elem.text if title_elem is not None and title_elem.text else "Untitled Position"
                link = ""
                if link_elem is not None:
                    link = link_elem.text or link_elem.attrib.get("href", "")
                description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                posted_date = pub_elem.text if pub_elem is not None and pub_elem.text else ""

                company = "Unknown Company"
                if " at " in title:
                    parts = title.split(" at ", 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                elif " - " in title:
                    parts = title.split(" - ", 1)
                    title = parts[0].strip()
                    company = parts[1].strip()

                jobs.append(
                    Job(
                        title=title,
                        company=company,
                        description=description,
                        location="Remote",
                        country=self.default_country,
                        work_mode="remote",
                        source=self.name,
                        application_url=link,
                        source_url=link,
                        posted_date=posted_date,
                    )
                )
        except Exception as e:
            logger.error(f"Error fetching RSS job source {self.name}: {e}")
        return jobs
