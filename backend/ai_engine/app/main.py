"""AI Engine Service — all LLM interactions for kit generation."""

from fastapi import FastAPI

from backend.ai_engine.app.config import get_settings
from backend.ai_engine.app.routes import generate, analyze

settings = get_settings()

app = FastAPI(
    title="InterviewKit AI — AI Engine Service",
    version="0.1.0",
)

app.include_router(analyze.router, tags=["Analyze"])
app.include_router(generate.router, tags=["Generate"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai_engine", "version": "0.1.0"}
