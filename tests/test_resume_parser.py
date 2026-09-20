from __future__ import annotations

import pytest
from app.services.resume import extract_resume_text, build_profile_from_resume, resume_status


def test_resume_text_validation():
    with pytest.raises(ValueError, match="Upload a PDF, DOCX, TXT, or MD resume."):
        extract_resume_text("test.exe", b"invalid")

    with pytest.raises(ValueError, match="could not be read"):
        extract_resume_text("test.txt", b"too short")


def test_build_profile_from_resume():
    sample_text = (
        "John Doe\n"
        "Email: john@example.com\n"
        "Skills: Python, FastAPI, PyTorch, Docker, RAG, pgvector, LLMs\n" + " " * 200
    )
    profile = build_profile_from_resume(sample_text, "john_resume.txt")
    assert profile["resume_file"] == "john_resume.txt"
    assert profile["resume_loaded"] is True
    assert "Python" in profile["skills"]
    assert "FastAPI" in profile["skills"]

    status = resume_status()
    assert status["loaded"] is True
    assert status["filename"] == "john_resume.txt"
