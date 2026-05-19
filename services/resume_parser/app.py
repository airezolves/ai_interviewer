"""Resume Parser service FastAPI application."""

from fastapi import FastAPI

from shared.middleware.error_handler import register_error_handlers
from shared.utils.logger import setup_logging
from services.resume_parser.config.settings import get_resume_parser_settings
from services.resume_parser.routes import router

settings = get_resume_parser_settings()
setup_logging(settings.SERVICE_NAME, settings.DEBUG)

app = FastAPI(
    title=f"{settings.APP_NAME} - Resume Parser Service",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
)

app.state.is_production = settings.is_production
register_error_handlers(app)
app.include_router(router)
