from __future__ import annotations

from app.models.schemas import Job
from app.services.deduplication import compute_dedup_hash, deduplicate_jobs


def test_deduplication_by_external_id():
    j1 = Job(external_id="123", source="RemoteOK", title="AI Intern", company="Acme")
    j2 = Job(external_id="123", source="RemoteOK", title="AI Intern (Duplicate)", company="Acme")

    h1 = compute_dedup_hash(j1)
    h2 = compute_dedup_hash(j2)
    assert h1 == h2

    unique, dup_count = deduplicate_jobs([j1, j2])
    assert len(unique) == 1
    assert dup_count == 1


def test_deduplication_by_url():
    j1 = Job(title="AI Intern", company="Acme", application_url="https://acme.com/jobs/1?ref=rss")
    j2 = Job(title="AI Intern", company="Acme", application_url="https://acme.com/jobs/1?source=board")

    h1 = compute_dedup_hash(j1)
    h2 = compute_dedup_hash(j2)
    assert h1 == h2


def test_deduplication_different_jobs():
    j1 = Job(title="AI Intern", company="Acme Corp", location="Bengaluru")
    j2 = Job(title="ML Engineer Intern", company="Beta Inc", location="Chennai")

    h1 = compute_dedup_hash(j1)
    h2 = compute_dedup_hash(j2)
    assert h1 != h2

    unique, dup_count = deduplicate_jobs([j1, j2])
    assert len(unique) == 2
    assert dup_count == 0
