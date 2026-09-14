from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class SearchSource:
    name: str
    url_template: str


SOURCES = [
    SearchSource("LinkedIn", "https://www.linkedin.com/jobs/search/?keywords={q}&location={location}"),
    SearchSource("Indeed", "https://www.indeed.com/jobs?q={q}&l={location}"),
    SearchSource("Wellfound", "https://wellfound.com/jobs"),
    SearchSource("Internshala", "https://internshala.com/internships/"),
]


def build_search_urls(keywords: list[str], locations: list[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for source in SOURCES:
        for keyword in keywords:
            for location in locations:
                results.append(
                    {
                        "source": source.name,
                        "keyword": keyword,
                        "location": location,
                        "url": source.url_template.format(
                            q=quote_plus(keyword), location=quote_plus(location)
                        ),
                    }
                )
    return results
