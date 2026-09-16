from __future__ import annotations

import pytest
from app.services.resume import extract_resume_text, parse_resume_fields, build_profile_from_resume


def test_resume_text_validation():
    with pytest.raises(ValueError, match="Unsupported format"):
        extract_resume_text("test.exe", b"invalid")

    with pytest.raises(ValueError, match="could not be extracted"):
        extract_resume_text("test.txt", b"too short")


def test_parse_resume_fields():
    sample_text = """
    Ranjith S
    Email: ranjith@example.com
    Phone: +91 9876543210
    Location: Chennai, India
    Education: B.Sc. Artificial Intelligence & Machine Learning, 2027
    University: SRM Institute of Science and Technology
    CGPA: 8.25

    Skills:
    Python, FastAPI, RAG, pgvector, PyTorch, Docker, OpenAI API, LLMs

    Projects:
    Built an evidence-first RAG business analysis system with pgvector and FastAPI.
    """
    fields = parse_resume_fields(sample_text)
    assert fields["name"] == "Ranjith S"
    assert fields["email"] == "ranjith@example.com"
    assert "Python" in fields["skills"]
    assert "FastAPI" in fields["skills"]
    assert "RAG" in fields["skills"]


def test_build_profile_from_resume():
    sample_text = "John Doe\nEmail: john@example.com\nPython FastAPI ML Intern 2027"
    profile = build_profile_from_resume(sample_text, "john_resume.txt")
    assert profile["resume_filename"] == "john_resume.txt"
    assert profile["resume_loaded"] is True
