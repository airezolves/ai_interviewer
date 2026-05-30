"""Auth Service — user management, authentication, usage tracking."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.auth.app.config import get_settings
from backend.auth.app.routes import auth, users, llm_providers
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
    title="InterviewKit AI — Auth Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router, tags=["Auth"])
app.include_router(users.router, tags=["Users"])
app.include_router(llm_providers.router, tags=["LLM Providers"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth", "version": "0.1.0"}
