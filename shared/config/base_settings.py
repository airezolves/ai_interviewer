"""
Base settings loaded from .env file.
All service-specific configs extend this.
"""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    """Find .env file - looks in ai_interviewer root."""
    current = Path(__file__).resolve()
    # Walk up to find .env at the ai_interviewer root
    for parent in current.parents:
        env_path = parent / ".env"
        if env_path.exists():
            return str(env_path)
        if parent.name == "ai_interviewer":
            return str(env_path)
    return ".env"


class BaseAppSettings(BaseSettings):
    """Base settings shared across all services."""

    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "InterviewKit AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interviewkit"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/interviewkit"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI/LLM
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "anthropic"
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"

    # File Storage
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Service URLs
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    RESUME_PARSER_URL: str = "http://localhost:8002"
    AI_ENGINE_URL: str = "http://localhost:8003"
    KIT_MANAGER_URL: str = "http://localhost:8004"
    PDF_GENERATOR_URL: str = "http://localhost:8005"
    BILLING_SERVICE_URL: str = "http://localhost:8006"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache()
def get_base_settings() -> BaseAppSettings:
    return BaseAppSettings()
