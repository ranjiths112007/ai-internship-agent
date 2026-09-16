# AI Internship Agent — Job Command Center & Application Assistant

Production-oriented **AI Internship Discovery, Matching, Application Tracking & Safe Browser Assistance System** optimized for AI/ML Engineer candidates.

---

## 🏗️ Product Architecture

```text
USER
  ↓
RESUME UPLOAD (PDF / DOCX / TXT / MD)
  ↓
RESUME PARSER & SECTIONS EXTRACTION
  ↓
PERSISTENT CANDIDATE PROFILE
  ↓
REAL JOB SOURCES (Apify / JSearch / RSS)
  ↓
JOB NORMALIZATION & CANONICAL SCHEMA
  ↓
MULTI-SIGNAL DEDUPLICATION
  ↓
AI RELEVANCE GATE & RESUME MATCHING
  ↓
JOB COMMAND CENTER DASHBOARD
  ├── Interactive Job Cards
  ├── Live Source Health Monitor
  ├── Application Lifecycle Tracker
  ├── JD Analysis & Answer Generator
  └── Safe Browser Assistance
```

---

## 🚀 Quick Start

### 1. Launching on Windows
Double-click `run_dashboard.bat` or execute in PowerShell:

```powershell
.\run_dashboard.bat
```

Or manually:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.init
python -m app.main
```

Dashboard URL: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)  
API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ⚡ Key Production Features

1. **Zero Fake/Demo Data**:
   - Production startup initializes an empty database (`0` stored jobs).
   - "Clear Jobs" button in the dashboard enables resetting stale stored jobs.

2. **Resume Upload Engine**:
   - Accepts PDF, DOCX, TXT, and MD files up to 8 MB.
   - Parses candidate Name, Email, Phone, Location, Degree, University, Graduation Year, CGPA/GPA, Skills, Projects, and Experience.
   - Automatically updates candidate search profile.

3. **Real Job Source Adapters**:
   - **Apify Scraper (`ApifyJobSource`)**: Uses `APIFY_API_KEY` to run Google Jobs and LinkedIn scrapers.
   - **JSearch API (`JSearchJobSource`)**: Uses `OPENWEBNINJA_API_KEY` for real-time job searches.
   - **RSS Feeds (`RSSJobSource`)**: Ingests active tech feeds (WeWorkRemotely, Remotive).

4. **AI Relevance Gate & Resume Matching**:
   - Caps non-AI generic software roles.
   - Penalizes 3+ years senior roles for intern candidates.
   - Detects location constraints (e.g. US-only remote warnings).

5. **Source Health Monitor & Discovery Logs**:
   - Real-time adapter statuses (`● Connected`, `● Not configured`, `● Failed`).

---

## ⚙️ Environment Configuration (`.env`)

```env
APP_ENV=development
DATABASE_URL=sqlite:///./data/internships.db

# Job Discovery API Keys
OPENWEBNINJA_API_KEY=your_key_here
APIFY_API_KEY=your_key_here
APIFY_GOOGLE_JOBS_ACTOR=apify/google-jobs-scraper
APIFY_LINKEDIN_JOBS_ACTOR=curious_coder/linkedin-jobs-scraper

# LLM Keys (Optional for deep analysis)
OPENAI_API_KEY=
GOOGLE_API_KEY=
LLM_PROVIDER=auto

DISCOVERY_ENABLED=false
DISCOVERY_INTERVAL_HOURS=6
PLAYWRIGHT_HEADLESS=true
APPLICATION_AUTOMATION_ENABLED=false
```

---

## 🧪 Running Tests

```bash
python -m pytest
```

---

## 🔒 Human-in-the-Loop Safety Notice
The browser automation layer is intentionally non-intrusive. Sensitive steps (CAPTCHAs, OTP/2FA, identity verification, assessments) stop for manual candidate review and submission.
