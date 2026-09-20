# AI Internship Agent

Production-oriented **AI Internship Discovery, Matching, Application Tracking & Safe Browser Assistance System** optimized for AI/ML Engineer candidates.

## 🎯 What this actually does

The app has two parts:

1. **FastAPI backend** — discovers, normalizes, deduplicates, scores and stores jobs.
2. **Browser dashboard** — lets you see companies/jobs, filter matches, inspect details, open applications, and track applications.

It is intentionally **not** a blind auto-apply bot. CAPTCHA, OTP/2FA, assessments, payment/ID fields and other sensitive steps stop the browser workflow for manual action.

## 🚀 Easiest way to run it on Windows

After cloning/downloading the repository, double-click:

```text
run_dashboard.bat
```

It creates the virtual environment, installs dependencies, starts the FastAPI server, and opens:

`http://127.0.0.1:8000/dashboard`

You can also start it manually:

```bash
python -m app.main
```

Then open `http://127.0.0.1:8000/dashboard`.

**Important:** `python app/main.py` was not the intended user workflow before this launcher was added. The application now has a direct Python entry point and prints the dashboard URL when started.

## 🔎 How job discovery works

```text
RSS / JSON / JSearch Job Sources
             ↓
Validation + Normalization + Skill Extraction
             ↓
Multi-Signal Deduplication
             ↓
Candidate Matching / Scoring
             ↓
SQLite Persistence
             ↓
Dashboard
```

Open the dashboard and click **Run discovery**. Only jobs returned by configured real sources are displayed. The app does not invent companies when a source returns nothing.

For JSearch, configure its API key in `.env` when you want that source enabled. RSS sources can work without a JSearch key when they are reachable.

## 🎯 Current candidate profile

- **Candidate**: B.Sc. Artificial Intelligence & Machine Learning, Grad 2027, CGPA 8.2
- **Target roles**: AI Engineer, Generative AI, Applied AI, ML Engineer, AI/ML Software Engineer, LLM Engineer, RAG Engineer, AI Agent Engineer internships
- **Target Indian cities**: Bengaluru, Chennai, Coimbatore
- **International remote lane**: Enabled only when a source explicitly indicates international/global remote scope
- **Stipend target**: INR 40,000/month

## 🖥️ Dashboard

The dashboard is deliberately built as a product UI rather than a terminal report:

- job discovery command
- searchable job cards
- match scores
- company, location, source and compensation
- skill chips
- job detail modal
- direct application links
- application tracker
- candidate profile view
- responsive mobile layout
- clear empty/error states

The visual direction follows practical shipped-product principles: restrained dark surfaces, strong typography, compact information density, consistent spacing, keyboard-friendly actions, and a clear primary action. This is closer to real product interfaces than a generic gradient-heavy AI landing page.

## 🐳 Docker

```bash
docker-compose up --build -d
```

The application listens on port 8000.

## 🧪 Tests

```bash
pytest tests/ -v
```

CI runs compilation, database initialization and the full pytest suite with deterministic LLM behavior and discovery/browser automation disabled.

## 🔒 Human-in-the-loop

The browser layer is deliberately **not** a bot-bypass or blind auto-apply system. A clean form can be inspected and mapped to candidate data, but the system does not claim that an external employer accepted an application. Final submission remains manual.
