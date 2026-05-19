"""AI Engine service configuration."""

from functools import lru_cache
from shared.config.base_settings import BaseAppSettings


class AIEngineSettings(BaseAppSettings):
    """AI Engine specific settings."""

    SERVICE_NAME: str = "ai_engine"
    SERVICE_PORT: int = 8003

    # LLM Configuration
    MAX_TOKENS_QUESTIONS: int = 4000
    MAX_TOKENS_ASSESSMENT: int = 5000
    MAX_TOKENS_RUBRIC: int = 3000
    MAX_TOKENS_RED_FLAGS: int = 2000
    MAX_TOKENS_FLOW_GUIDE: int = 2000

    # Generation settings
    TEMPERATURE: float = 0.7
    MAX_RETRIES: int = 3


@lru_cache()
def get_ai_engine_settings() -> AIEngineSettings:
    return AIEngineSettings()
