# AI Internship Agent

Production-quality **AI Internship Discovery, Matching, Application Tracking & Safe Browser Automation System** optimized for AI/ML Engineer candidates.

---

## 🎯 Target Candidate Profile

- **Candidate**: Ranjith S (B.Sc. Artificial Intelligence & Machine Learning, Grad 2027, CGPA 8.2)
- **Target Roles**:
  - AI Engineer Intern / Generative AI Intern / Applied AI Intern
  - Machine Learning Engineer Intern / AI/ML Engineer Intern
  - Software Engineer Intern — AI/ML / LLM Engineer Intern
  - RAG Engineer Intern / AI Agent Engineer Intern
- **Target Indian Cities**: Bengaluru, Chennai, Coimbatore
- **International Remote Lane**: Enabled (Worldwide Remote, Global Startups, Unrestricted Remote)
- **Stipend Target**: Minimum INR 40,000 / month

---

## 🏗️ System Architecture

```text
Job Sources (RSS / JSON / Career Pages)
                ↓
    Job Ingestion & Normalization (Titles, Remote Category, Stipend)
                ↓
        Multi-Signal Deduplication (Source ID / Canonical URL / Hash)
                ↓
    Multi-Layer Scoring Engine (Role, Skill Match, Evidence, Seniority, Stipend)
                ↓
    LLM JD Analysis & Candidate Question Generator (Gemini / OpenAI / Fallback)
                ↓
    SQLite Database Persistence (Jobs & Application Lifecycle Tracking)
                ↓
    Executive Web Dashboard & REST API
                ↓
    Playwright Browser Safety & Pre-fill (Halts on CAPTCHA / 2FA / Human confirmation)
```

---

## 🔒 Absolute Safety & Human-In-The-Loop Rules

The browser automation layer strictly enforces safety controls:
1. **Automated Safety Halts (`MANUAL_ACTION_REQUIRED`)**: Halts execution and notifies the user whenever encountering:
   - CAPTCHAs / Cloudflare security challenges
   - 2FA / OTP phone verification
   - Coding assessments / Personality tests
   - Government ID / Payment / Credit card forms
2. **Explicit Human Confirmation**: Pre-fills application forms safely and STOPS before submission. Submission requires explicit user confirmation via `POST /api/browser/submit`.

---

## 🚀 Quick Start

### Local Setup

```bash
# 1. Create virtual environment
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Environment configuration
copy .env.example .env

# 4. Initialize Database
python -m app.db.init

# 5. Start Application Server
uvicorn app.main:app --reload
```

Open Dashboard: http://127.0.0.1:8000/
Open API Docs: http://127.0.0.1:8000/docs

---

### Docker Setup

```bash
docker-compose up --build -d
```

Access the dashboard at `http://localhost:8000/`.

---

## 🧪 Running Automated Tests

```bash
pytest tests/ -v
```

The test suite covers:
- `test_scoring.py`: Role matching, seniority penalties, stipend matching, international remote lane.
- `test_deduplication.py`: Deduplication by external ID, URL, and metadata hash.
- `test_persistence.py`: SQLite CRUD operations on jobs and application state.
- `test_api.py`: FastAPI endpoints.
- `test_llm_fallback.py`: Deterministic fallback parser when API keys are empty.
- `test_browser_safety.py`: DOM safety checks and human confirmation enforcement.

---

## 🌐 API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service health status |
| `GET` | `/api/profile` | Candidate profile & preferences |
| `POST` | `/api/score` | Score a job against candidate profile |
| `GET` | `/api/discovery/urls` | Discovery search template URLs |
| `POST` | `/api/discovery/run` | Execute job discovery pipeline across sources |
| `GET` | `/api/jobs` | Query discovered jobs with score & location filters |
| `GET` | `/api/jobs/{id}` | Detailed job view with score breakdown & LLM analysis |
| `POST` | `/api/analyze/job` | Run LLM / Fallback structured JD analysis |
| `POST` | `/api/applications` | Save job to application tracker |
| `GET` | `/api/applications` | List applications by status |
| `PATCH` | `/api/applications/{id}` | Update application status or answers |
| `POST` | `/api/applications/questions/generate` | Generate candidate-grounded application answers |
| `POST` | `/api/browser/prepare` | Inspect form & pre-fill fields |
| `POST` | `/api/browser/submit` | Submit application upon human confirmation |

---

## 🔌 Adding a New Job Source

To add a new job source adapter:
1. Create a new subclass of `JobSource` in `app/sources/`.
2. Implement `fetch_jobs(self) -> list[Job]`.
3. Register the instance in `app/sources/registry.py` under `get_default_sources()`.

---

## 📊 Status Matrix

| Component | Status | Implementation Details |
|-----------|--------|------------------------|
| Candidate Profile | Implemented | Grounded in `config/candidate_profile.json` |
| Job Ingestion Adapters | Implemented | RSS, JSON feed, Curated Career sources |
| Normalization & Deduplication | Implemented | Multi-signal deduplication & remote lane classification |
| Multi-Layer Scoring | Implemented | Role, skill, evidence, seniority, stipend, location |
| LLM Analysis & Fallback | Implemented | Gemini, OpenAI & Deterministic Fallback |
| Question Generator | Implemented | Grounded in candidate profile & evidence |
| Application Tracker | Implemented | Full lifecycle (`saved`, `preparing`, `applied`, `interview`, `offer`) |
| Scheduled Discovery | Implemented | Configurable background scheduler |
| Browser Safety Automation | Implemented | Safe form inspection & human-in-the-loop confirmation |
| Executive Dashboard | Implemented | Single-page glassmorphism web interface |
| Docker & Tests | Implemented | Dockerfile, docker-compose, pytest suite |
