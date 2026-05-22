"""Resume service configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class ResumeSettings(BaseAppSettings):
    """Resume-specific settings."""
    service_name: str = "resume"
    service_port: int = 8002
    max_file_size_mb: int = 10
    anthropic_api_key: str = ""
    openai_api_key: str = ""


@lru_cache()
def get_settings() -> ResumeSettings:
    return ResumeSettings()
