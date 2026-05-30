"""Resume Service — PDF/DOCX parsing and structuring."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.resume.app.config import get_settings
from backend.resume.app.routes import parse
from shared.database import init_database

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database connection
    init_database(settings.database_url, echo=settings.debug)
    yield
    # Shutdown: close database connection
    from shared.database import get_database
    await get_database().close()


app = FastAPI(
    title="InterviewKit AI — Resume Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(parse.router, tags=["Parse"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "resume", "version": "0.1.0"}
