"""Export Service — PDF generation and shareable links."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.export.app.config import get_settings
from backend.export.app.routes import pdf, share
from shared.database import init_database

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database(settings.database_url, echo=settings.debug)
    yield
    from shared.database import get_database
    await get_database().close()


app = FastAPI(
    title="InterviewKit AI — Export Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(pdf.router, tags=["PDF"])
app.include_router(share.router, tags=["Share"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "export", "version": "0.1.0"}
