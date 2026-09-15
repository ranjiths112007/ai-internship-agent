from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.metrics import router as metrics_router
from app.api.routes import router
from app.db.init import init_db
from app.services.scheduler import start_discovery_scheduler, stop_discovery_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_discovery_scheduler()
    try:
        yield
    finally:
        stop_discovery_scheduler()


app = FastAPI(
    title="AI Internship Agent",
    version="1.1.0",
    description=(
        "AI-powered internship discovery, matching, application tracking, "
        "dashboard metrics, and safe human-supervised browser assistance."
    ),
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")
app.include_router(metrics_router, prefix="/api")

DASHBOARD_PATH = Path(__file__).parent / "dashboard" / "index.html"


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    if DASHBOARD_PATH.exists():
        return HTMLResponse(content=DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<h1>AI Internship Agent</h1><p>API is running. Visit <a href='/docs'>/docs</a>.</p>"
    )


@app.get("/api-status")
def status() -> dict[str, str]:
    return {
        "name": "AI Internship Agent",
        "status": "running",
        "version": "1.1.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "metrics": "/api/metrics",
    }
