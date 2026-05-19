"""PDF Generator service configuration."""

from functools import lru_cache
from shared.config.base_settings import BaseAppSettings


class PDFGeneratorSettings(BaseAppSettings):
    """PDF Generator specific settings."""

    SERVICE_NAME: str = "pdf_generator"
    SERVICE_PORT: int = 8005

    OUTPUT_DIR: str = "./data/outputs"
    TEMPLATE_DIR: str = "./services/pdf_generator/templates"
    PDF_CACHE_TTL_HOURS: int = 24


@lru_cache()
def get_pdf_generator_settings() -> PDFGeneratorSettings:
    return PDFGeneratorSettings()
