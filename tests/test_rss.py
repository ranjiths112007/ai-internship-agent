from __future__ import annotations

import httpx
import pytest

from app.sources.rss import RSSJobSource

SAMPLE_RSS = """<rss><channel>
<item>
  <title>AI Engineer Intern at Acme</title>
  <link>https://acme.com/job/1</link>
  <description>Build RAG systems</description>
  <pubDate>Mon, 01 Sep 2025 00:00:00 GMT</pubDate>
  <guid>acme-1</guid>
</item>
<item>
  <title>ML Intern - Beta Corp</title>
  <link>https://beta.com/job/2</link>
</item>
<item>
  <title>Missing link is skipped</title>
</item>
</channel></rss>"""

SAMPLE_ATOM = """<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
  <title>Remote AI Intern at Gamma Labs</title>
  <link href="https://gamma.com/job/3"/>
  <summary>Remote-first AI internship</summary>
  <id>gamma-3</id>
</entry>
</feed>"""


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_rss_source_parses_plain_leaf_elements(monkeypatch):
    """Regression test: item.find(a) or item.find(b) is falsy for text-only
    leaf elements (ET.Element truthiness is based on child count), which
    previously made every RSS item look like it had no title/link and get
    silently skipped. This must correctly extract real feed data."""
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: _FakeResponse(SAMPLE_RSS))
    source = RSSJobSource(name="TestFeed", url="https://example.com/feed.rss")
    jobs = source.fetch_jobs()

    assert len(jobs) == 2  # the item missing a link must be skipped
    assert jobs[0].title == "AI Engineer Intern"
    assert jobs[0].company == "Acme"
    assert jobs[0].application_url == "https://acme.com/job/1"
    assert jobs[0].description == "Build RAG systems"
    assert jobs[1].title == "ML Intern"
    assert jobs[1].company == "Beta Corp"


def test_rss_source_parses_atom_feeds(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: _FakeResponse(SAMPLE_ATOM))
    source = RSSJobSource(name="TestAtomFeed", url="https://example.com/feed.atom")
    jobs = source.fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].title == "Remote AI Intern"
    assert jobs[0].company == "Gamma Labs"
    assert jobs[0].application_url == "https://gamma.com/job/3"


def test_rss_source_returns_empty_on_http_failure(monkeypatch):
    def _raise(*a, **kw):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "get", _raise)
    source = RSSJobSource(name="TestFeed", url="https://example.com/feed.rss")
    assert source.fetch_jobs() == []
