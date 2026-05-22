"""Kit Orchestrator Service — pipeline coordination."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.kit_orchestrator.app.config import get_settings
from backend.kit_orchestrator.app.routes import generate, kits
from shared.database import init_database

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database(settings.database_url, echo=settings.debug)
    yield
    from shared.database import get_database
    await get_database().close()


app = FastAPI(
    title="InterviewKit AI — Kit Orchestrator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(generate.router, tags=["Generate"])
app.include_router(kits.router, tags=["Kits"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kit_orchestrator", "version": "0.1.0"}
