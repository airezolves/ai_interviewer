"""Resume Parser service configuration."""

from functools import lru_cache
from shared.config.base_settings import BaseAppSettings


class ResumeParserSettings(BaseAppSettings):
    """Resume parser specific settings."""

    SERVICE_NAME: str = "resume_parser"
    SERVICE_PORT: int = 8002

    # Parsing limits
    MAX_RESUME_PAGES: int = 20
    MAX_RESUME_SIZE_MB: int = 10
    SUPPORTED_FORMATS: str = "pdf,docx"

    @property
    def supported_formats_list(self) -> list[str]:
        return [f.strip() for f in self.SUPPORTED_FORMATS.split(",")]


@lru_cache()
def get_resume_parser_settings() -> ResumeParserSettings:
    return ResumeParserSettings()
