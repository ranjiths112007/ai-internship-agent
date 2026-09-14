from __future__ import annotations

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.db.init import init_db
from app.services.scheduler import start_discovery_scheduler, stop_discovery_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init DB tables & start discovery scheduler
    init_db()
    start_discovery_scheduler()
    yield
    # Shutdown: Stop scheduler
    stop_discovery_scheduler()


app = FastAPI(
    title="AI Internship Agent",
    version="1.0.0",
    description="AI-powered internship discovery, matching, application tracking, and safe browser automation system.",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")

DASHBOARD_PATH = Path(__file__).parent / "dashboard" / "index.html"


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    if DASHBOARD_PATH.exists():
        return HTMLResponse(content=DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AI Internship Agent API Running</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>")


@app.get("/api-status")
def status() -> dict[str, str]:
    return {
        "name": "AI Internship Agent",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }
