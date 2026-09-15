# AI Internship Agent

Production-oriented **AI Internship Discovery, Matching, Application Tracking & Safe Browser Assistance System** optimized for AI/ML Engineer candidates.

## 🎯 Target Candidate Profile

- **Candidate**: B.Sc. Artificial Intelligence & Machine Learning, Grad 2027, CGPA 8.2
- **Target roles**: AI Engineer, Generative AI, Applied AI, ML Engineer, AI/ML Software Engineer, LLM Engineer, RAG Engineer, AI Agent Engineer internships
- **Target Indian cities**: Bengaluru, Chennai, Coimbatore
- **International remote lane**: Enabled, but only when a source explicitly indicates a non-India remote scope
- **Stipend target**: Minimum INR 40,000/month

## 🏗️ Architecture

```text
RSS / JSON / JSearch Job Sources
             ↓
Validation + Normalization + Skill Extraction
             ↓
Multi-Signal Deduplication
             ↓
Candidate Matching / Scoring
             ↓
Optional LLM JD Analysis + Deterministic Fallback
             ↓
SQLite Persistence
             ↓
FastAPI + Dashboard + Application Tracker
             ↓
Safe Browser Inspection → Manual Review → Manual Submission
```

## 🔒 Safety / Human-in-the-Loop

The browser layer is deliberately **not** a bot-bypass or blind auto-apply system.

It stops for CAPTCHA/security challenges, OTP/2FA, assessments/tests, government ID, payment/credit-card fields, and other sensitive interactions. A clean form can be inspected and mapped to candidate data, but the system does not claim that an external employer accepted an application. Final submission remains manual.

## 🚀 Quick Start

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Windows
copy .env.example .env

# macOS/Linux
# cp .env.example .env

python -m app.db.init
uvicorn app.main:app --reload
```

Dashboard: `http://127.0.0.1:8000/`

API docs: `http://127.0.0.1:8000/docs`

## 🐳 Docker

```bash
docker-compose up --build -d
```

The application listens on port 8000.

## 🧪 Tests

```bash
pytest tests/ -v
```

CI also runs compilation, database initialization, and the full pytest suite with deterministic LLM behavior and discovery/browser automation disabled.

Coverage includes scoring, normalization, deduplication, JSearch parsing/error handling, persistence, API lifecycle tests, LLM fallback, browser safety, and manual-submission enforcement.

## 🌐 API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Database / provider health |
| GET | `/api/profile` | Candidate profile |
| POST | `/api/score` | Score a supplied job |
| GET | `/api/discovery/urls` | Build navigational search URLs |
| POST | `/api/discovery/run` | Run registered discovery adapters |
| GET | `/api/jobs` | Filter/sort persisted jobs |
| POST | `/api/jobs` | Normalize, score and persist a job |
| GET | `/api/jobs/{id}` | Job detail |
| POST | `/api/analyze/job` | Structured JD analysis |
| GET | `/api/metrics` | Persisted pipeline/application metrics |
| POST | `/api/applications` | Create tracked application |
| GET | `/api/applications` | List tracked applications |
| GET | `/api/applications/{id}` | Application detail |
| PATCH | `/api/applications/{id}` | Update application lifecycle |
| POST | `/api/applications/questions/generate` | Candidate-grounded answers |
| POST | `/api/browser/prepare` | Inspect application form safely |
| POST | `/api/browser/submit` | Confirm local readiness for manual submission; never fakes external submission |

## 🔌 Job Sources

Production discovery uses real adapters configured in `app/sources/registry.py`. Sources that cannot provide a real listing are not used as fake production data.

To add a source:

1. Create a `JobSource` subclass under `app/sources/`.
2. Implement `fetch_jobs() -> list[Job]`.
3. Validate title/company/application URL and preserve source currency.
4. Register the adapter in `get_default_sources()`.
5. Add parser and failure-path tests.

## 📊 Implementation Status

| Component | Status |
|---|---|
| Candidate profile | Implemented |
| Real job ingestion adapters | Implemented |
| Validation / normalization | Implemented |
| Deduplication | Implemented |
| Candidate scoring | Implemented |
| LLM + deterministic fallback | Implemented |
| JD analysis | Implemented |
| Application answer generation | Implemented |
| Application lifecycle tracker | Implemented |
| Scheduled discovery | Implemented |
| Browser form inspection | Implemented |
| Safety halts / manual review | Implemented |
| Dashboard | Implemented |
| Metrics API | Implemented |
| Docker | Implemented |
| Automated regression suite | Implemented |
| CI verification | Continuously verified by GitHub Actions |

## ⚠️ Important Production Notes

- Discovery is disabled by default until real source/API configuration is supplied.
- Application automation is disabled by default.
- Foreign salaries are not silently converted to INR without a configured FX rate.
- The repository does not manufacture successful applications, fabricated job listings, or fabricated candidate contact details.
