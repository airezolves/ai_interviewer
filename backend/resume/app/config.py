"""Resume service configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class ResumeSettings(BaseAppSettings):
    """Resume-specific settings."""
    service_name: str = "resume"
    service_port: int = 8002
    max_file_size_mb: int = 10
    
    # LiteLLM model configuration (supports any provider)
    llm_provider: str = "gemini"  # Options: anthropic, openai, gemini
    llm_model: str = "gemini-2.5-flash"
    
    # API keys (only needed for the provider you're using)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""


@lru_cache()
def get_settings() -> ResumeSettings:
    return ResumeSettings()
