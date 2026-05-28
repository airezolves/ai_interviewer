"""Export service configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class ExportSettings(BaseAppSettings):
    """Export-specific settings."""
    service_name: str = "export"
    service_port: int = 8005
    storage_local_path: str = "./data/exports"
    gateway_url: str = "http://localhost:8000"  # Gateway URL for building download URLs


@lru_cache()
def get_settings() -> ExportSettings:
    return ExportSettings()
