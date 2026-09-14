# AI Internship Agent

AI-assisted internship discovery, matching, application tracking, and browser automation system.

## MVP
- Structured candidate profile and preferences
- Deterministic job-fit scoring
- FastAPI service
- SQLite local persistence
- SQLAlchemy models
- Environment-based configuration
- Extension points for job sources, LLM matching, and browser automation

## Target
- AI Engineer / GenAI / Applied AI / ML Engineer / AI-ML Software Engineer internships
- Chennai, Bengaluru, Coimbatore
- Remote opportunities worldwide, including international startups
- Stipend target: INR 40,000/month and above
- Strong preference for real engineering work and useful internship perks

## Quick start

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Roadmap
1. Candidate profile + scoring engine
2. Job ingestion adapters
3. Deduplication and persistence
4. LLM semantic matching
5. Opportunity ranking
6. Application-question generation
7. Playwright browser automation
8. Application tracking dashboard
9. Scheduled discovery and notifications
10. International remote/startup expansion

The agent must stop for CAPTCHAs, identity verification, assessments, or other interactions requiring user input rather than attempting to bypass anti-bot protections.
