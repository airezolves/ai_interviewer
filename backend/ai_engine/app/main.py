"""AI Engine Service — match / interview / analysis agents."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.ai_engine.app.config import get_settings
from backend.ai_engine.app.routes import v2
from shared.database import init_database, get_database

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database(settings.database_url, echo=False)
    yield
    await get_database().close()


app = FastAPI(
    title="InterviewKit AI — AI Engine Service",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(v2.router, tags=["v2"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai_engine", "version": "2.0.0"}
