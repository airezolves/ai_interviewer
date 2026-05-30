"""API Gateway Service — routing, auth verification, rate limiting."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.gateway.app.config import get_settings
from backend.gateway.app.routes import auth, kits, export, health, llm_providers
from backend.gateway.app.middleware.rate_limiter import RateLimitMiddleware

settings = get_settings()

app = FastAPI(
    title="InterviewKit AI — API Gateway",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(kits.router, prefix="/api/v1/kits", tags=["Kits"])
app.include_router(llm_providers.router, prefix="/api/v1/llm-providers", tags=["LLM Providers"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
