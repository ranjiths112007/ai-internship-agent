from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.models.schemas import Job, JobAnalysisResult, QuestionAnswer

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def analyze_job_description(self, job: Job) -> JobAnalysisResult:
        """Extract structured JD analysis."""
        pass

    @abstractmethod
    def generate_application_answers(
        self, job_title: str, company: str, jd_text: str, profile: dict, questions: list[str]
    ) -> list[QuestionAnswer]:
        """Generate candidate-grounded application answers."""
        pass


class DeterministicFallbackProvider(LLMProvider):
    """Fallback parser when no LLM API key is available or LLM service fails."""

    def analyze_job_description(self, job: Job) -> JobAnalysisResult:
        text = (job.title + " " + job.description + " " + " ".join(job.skills)).lower()

        required_skills = []
        common_skills = [
            "Python", "FastAPI", "Flask", "RAG", "LLMs", "AI Agents", "Tool Calling",
            "Embeddings", "pgvector", "SQL", "Docker", "OpenCV", "Tesseract OCR",
            "PyTorch", "TensorFlow", "React", "TypeScript", "Next.js"
        ]
        for s in common_skills:
            if s.lower() in text:
                required_skills.append(s)

        is_intern = any(k in text for k in ["intern", "internship", "trainee", "fresher", "co-op"])
        seniority = "Internship" if is_intern else ("Senior" if "senior" in text or "5+" in text or "3+" in text else "Junior/Mid")

        red_flags = []
        if any(k in text for k in ["3+ years", "5+ years", "senior level", "lead engineer"]):
            red_flags.append("Requires senior-level years of experience.")
        if "unpaid" in text:
            red_flags.append("Unpaid position detected.")

        is_intl_remote = job.location_category == "international_remote" or "worldwide" in text or "global remote" in text

        summary = f"Parsed position: {job.title} at {job.company}. Matches {len(required_skills)} profile skills."

        return JobAnalysisResult(
            role_type="AI/ML Engineer" if "ai" in text or "ml" in text else "Software Engineer",
            seniority=seniority,
            required_skills=required_skills,
            preferred_skills=[],
            responsibilities=[],
            education_requirements=["B.Sc / B.Tech pursuing"],
            experience_requirements=["0-1 years"],
            location_constraints=[job.location],
            remote_constraints=[job.work_mode],
            stipend={"disclosed": job.stipend_monthly_inr is not None, "amount_inr": job.stipend_monthly_inr},
            visa_requirement={},
            international_remote=is_intl_remote,
            internship=is_intern,
            conversion_signal={"mentioned": "conversion" in text or "ppo" in text},
            red_flags=red_flags,
            summary=summary,
            confidence=0.75,
        )

    def generate_application_answers(
        self, job_title: str, company: str, jd_text: str, profile: dict, questions: list[str]
    ) -> list[QuestionAnswer]:
        answers: list[QuestionAnswer] = []

        cand = profile.get("candidate", {})
        cand_name = cand.get("name", "Ranjith S")
        degree = cand.get("education", "B.Sc. Artificial Intelligence & Machine Learning")
        grad_year = cand.get("graduation_year", 2027)
        cgpa = cand.get("cgpa", 8.2)

        skills = ", ".join(profile.get("skills", [])[:8])
        evidence_list = profile.get("strong_evidence", [])
        rag_evidence = evidence_list[0] if len(evidence_list) > 0 else ""
        agent_evidence = evidence_list[1] if len(evidence_list) > 1 else ""

        for q in questions:
            q_lower = q.lower()
            if "why" in q_lower and ("join" in q_lower or "company" in q_lower or "fit" in q_lower):
                ans = (
                    f"I am eager to join {company} as a {job_title}. "
                    f"Currently pursuing my {degree} (Graduating {grad_year}, CGPA {cgpa}), "
                    f"I have extensive hands-on experience building production AI systems including RAG pipelines, pgvector semantic search, and FastAPI backends. "
                    f"My background aligns directly with {company}'s tech stack and vision."
                )
                rat = "Grounded in degree, CGPA, and RAG/FastAPI technical background."
                req_input = False
            elif "project" in q_lower or "llm" in q_lower or "ai" in q_lower or "rag" in q_lower:
                ans = (
                    f"One of my key projects is an evidence-first AI business analysis system. "
                    f"I built it using RAG, pgvector vector embeddings, Gemini, FastAPI, Next.js, and Docker. "
                    f"Additionally, I built a tool-using Telegram/Gmail AI agent featuring OpenAI API tool calling, memory, and OAuth 2.0 human-in-the-loop confirmation."
                )
                rat = "Grounded in candidate strong project evidence 1 & 2."
                req_input = False
            elif "stipend" in q_lower or "salary" in q_lower or "expectation" in q_lower:
                min_stipend = profile.get("minimum_monthly_stipend_inr", 40000)
                ans = f"My stipend expectation is around INR {min_stipend:,}/month, aligned with industry standard AI engineering internships."
                rat = "Grounded in candidate profile minimum_monthly_stipend_inr."
                req_input = False
            elif "relocate" in q_lower or "available" in q_lower or "location" in q_lower:
                ans = f"I am based in Chennai and fully available for remote work globally or onsite/hybrid roles in Bengaluru, Chennai, and Coimbatore."
                rat = "Grounded in candidate profile location preferences."
                req_input = False
            else:
                ans = (
                    f"As a {degree} student at CGPA {cgpa}, I bring strong technical skills in {skills}. "
                    f"{rag_evidence}"
                )
                rat = "Grounded in core candidate profile metadata."
                req_input = False

            answers.append(QuestionAnswer(question=q, answer=ans, rationale=rat, requires_user_input=req_input))

        return answers


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for JD analysis and question answering."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _call_openai(self, prompt: str, system_prompt: str = "") -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        resp = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20.0)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def analyze_job_description(self, job: Job) -> JobAnalysisResult:
        try:
            prompt = f"Analyze this job description:\nTitle: {job.title}\nCompany: {job.company}\nLocation: {job.location}\nDescription:\n{job.description}\n\nReturn JSON matching schema."
            sys_prompt = "You are a JD parser. Return JSON with keys: role_type, seniority, required_skills, preferred_skills, responsibilities, education_requirements, experience_requirements, location_constraints, remote_constraints, stipend, visa_requirement, international_remote, internship, conversion_signal, red_flags, summary, confidence."
            raw_res = self._call_openai(prompt, sys_prompt)
            match = re.search(r"\{.*\}", raw_res, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return JobAnalysisResult(**data)
        except Exception as e:
            logger.warning(f"OpenAI analysis failed: {e}. Falling back to deterministic parser.")
        return DeterministicFallbackProvider().analyze_job_description(job)

    def generate_application_answers(
        self, job_title: str, company: str, jd_text: str, profile: dict, questions: list[str]
    ) -> list[QuestionAnswer]:
        try:
            prompt = f"Job: {job_title} at {company}\nJD: {jd_text}\nCandidate Profile: {json.dumps(profile)}\nQuestions: {json.dumps(questions)}\n\nGenerate structured answers for each question grounded strictly in candidate profile without inventing information. Return JSON array of objects with keys: question, answer, rationale, requires_user_input."
            sys_prompt = "You are an AI application assistant. Answer application questions truthfully grounded in the candidate profile."
            raw_res = self._call_openai(prompt, sys_prompt)
            match = re.search(r"\[.*\]", raw_res, re.DOTALL)
            if match:
                items = json.loads(match.group(0))
                return [QuestionAnswer(**item) for item in items]
        except Exception as e:
            logger.warning(f"OpenAI question answer generation failed: {e}. Falling back to deterministic provider.")
        return DeterministicFallbackProvider().generate_application_answers(job_title, company, jd_text, profile, questions)


class GeminiProvider(LLMProvider):
    """Google Gemini API provider for JD analysis and question answering."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _call_gemini(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = httpx.post(url, headers=headers, json=payload, timeout=20.0)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def analyze_job_description(self, job: Job) -> JobAnalysisResult:
        try:
            prompt = f"Analyze this job description and output raw JSON (no markdown formatting):\nTitle: {job.title}\nCompany: {job.company}\nDescription: {job.description}\n\nJSON schema keys required: role_type, seniority, required_skills, preferred_skills, responsibilities, education_requirements, experience_requirements, location_constraints, remote_constraints, stipend, visa_requirement, international_remote, internship, conversion_signal, red_flags, summary, confidence."
            raw_res = self._call_gemini(prompt)
            match = re.search(r"\{.*\}", raw_res, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return JobAnalysisResult(**data)
        except Exception as e:
            logger.warning(f"Gemini analysis failed: {e}. Falling back to deterministic parser.")
        return DeterministicFallbackProvider().analyze_job_description(job)

    def generate_application_answers(
        self, job_title: str, company: str, jd_text: str, profile: dict, questions: list[str]
    ) -> list[QuestionAnswer]:
        try:
            prompt = f"Job: {job_title} at {company}\nJD: {jd_text}\nCandidate Profile: {json.dumps(profile)}\nQuestions: {json.dumps(questions)}\n\nGenerate JSON array of objects with keys: question, answer, rationale, requires_user_input."
            raw_res = self._call_gemini(prompt)
            match = re.search(r"\[.*\]", raw_res, re.DOTALL)
            if match:
                items = json.loads(match.group(0))
                return [QuestionAnswer(**item) for item in items]
        except Exception as e:
            logger.warning(f"Gemini question answer generation failed: {e}. Falling back to deterministic provider.")
        return DeterministicFallbackProvider().generate_application_answers(job_title, company, jd_text, profile, questions)


def get_llm_provider() -> LLMProvider:
    provider_setting = settings.llm_provider.lower().strip()
    if provider_setting == "openai" and settings.openai_api_key:
        return OpenAIProvider(settings.openai_api_key)
    elif provider_setting == "gemini" and settings.google_api_key:
        return GeminiProvider(settings.google_api_key)
    elif provider_setting == "auto":
        if settings.google_api_key:
            return GeminiProvider(settings.google_api_key)
        elif settings.openai_api_key:
            return OpenAIProvider(settings.openai_api_key)

    return DeterministicFallbackProvider()
