"""Shared base configuration. Each service extends this."""

from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv


# Project root (ai_interviewer/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Eager-load .env so os.getenv() also works for code paths not using BaseAppSettings.
load_dotenv(PROJECT_ROOT / ".env", override=False)


class BaseAppSettings(BaseSettings):
    """Base settings shared across all services."""

    # App
    app_name: str = "interviewkit-ai"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:devpassword@localhost:5432/interviewkit"
    database_url_sync: str = "postgresql://postgres:devpassword@localhost:5432/interviewkit"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "dev-secret-key-do-not-use-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Service URLs
    gateway_url: str = "http://localhost:8000"
    auth_service_url: str = "http://localhost:8001"
    resume_service_url: str = "http://localhost:8002"
    ai_engine_url: str = "http://localhost:8003"
    kit_orchestrator_url: str = "http://localhost:8004"
    export_service_url: str = "http://localhost:8005"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Encryption (AES-256-GCM master key for per-user LLM API key storage)
    ai_encryption_master_key: str = ""

    # LLM defaults (used when a user has no provider configured)
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-pro"
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"
