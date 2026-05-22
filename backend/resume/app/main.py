"""Resume Service — PDF/DOCX parsing and structuring."""

from fastapi import FastAPI

from backend.resume.app.config import get_settings
from backend.resume.app.routes import parse

settings = get_settings()

app = FastAPI(
    title="InterviewKit AI — Resume Service",
    version="0.1.0",
)

app.include_router(parse.router, tags=["Parse"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "resume", "version": "0.1.0"}
