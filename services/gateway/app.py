"""API Gateway — main entry point for all client requests."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.middleware.error_handler import register_error_handlers
from shared.utils.logger import setup_logging
from services.gateway.config.settings import get_gateway_settings
from services.gateway.middleware import RequestLoggingMiddleware
from services.gateway.routes import router

settings = get_gateway_settings()
setup_logging(settings.SERVICE_NAME, settings.DEBUG)

app = FastAPI(
    title=f"{settings.APP_NAME} - API Gateway",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Error handling
app.state.is_production = settings.is_production
register_error_handlers(app)

# Routes
app.include_router(router)
