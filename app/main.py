from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="AI Internship Agent",
    version="0.1.0",
    description="AI-assisted internship discovery and application matching system.",
)

app.include_router(router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "AI Internship Agent",
        "status": "running",
        "docs": "/docs",
    }
