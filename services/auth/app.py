"""Auth service FastAPI application."""

from fastapi import FastAPI

from shared.middleware.error_handler import register_error_handlers
from shared.utils.logger import setup_logging
from services.auth.config.settings import get_auth_settings
from services.auth.routes import router

settings = get_auth_settings()
setup_logging(settings.SERVICE_NAME, settings.DEBUG)

app = FastAPI(
    title=f"{settings.APP_NAME} - Auth Service",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
)

app.state.is_production = settings.is_production
register_error_handlers(app)
app.include_router(router)


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    pass
