from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.metrics import router as metrics_router
from app.api.routes import router
from app.db.init import init_db
from app.services.resume import resume_status
from app.services.scheduler import start_discovery_scheduler, stop_discovery_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_discovery_scheduler()
    try:
        yield
    finally:
        stop_discovery_scheduler()


app = FastAPI(title="AI Internship Agent", version="1.3.0", description="Real internship discovery, resume matching, tracking, and safe application assistance.", lifespan=lifespan)
app.include_router(router, prefix="/api")
app.include_router(metrics_router, prefix="/api")

DASHBOARD_PATH = Path(__file__).parent / "dashboard" / "index.html"
SETUP_PATH = Path(__file__).parent / "dashboard" / "setup.html"


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    path = DASHBOARD_PATH if resume_status()["loaded"] else SETUP_PATH
    return HTMLResponse(content=path.read_text(encoding="utf-8"))


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    return HTMLResponse(content=DASHBOARD_PATH.read_text(encoding="utf-8"))


@app.get("/api-status")
def status() -> dict[str, str]:
    return {"name": "AI Internship Agent", "status": "running", "version": "1.3.0", "docs": "/docs", "dashboard": "/dashboard"}


if __name__ == "__main__":
    import uvicorn
    print("\nAI Internship Agent is starting...")
    print("Open: http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
