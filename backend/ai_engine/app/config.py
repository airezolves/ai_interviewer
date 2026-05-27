"""AI Engine service configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class AIEngineSettings(BaseAppSettings):
    """AI Engine-specific settings."""
    service_name: str = "ai_engine"
    service_port: int = 8003
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    llm_primary_provider: str = "anthropic"  # Options: anthropic, openai, gemini
    llm_primary_model: str = "claude-sonnet-4-20250514"
    llm_fallback_provider: str = "openai"
    llm_fallback_model: str = "gpt-4o"


@lru_cache()
def get_settings() -> AIEngineSettings:
    return AIEngineSettings()
