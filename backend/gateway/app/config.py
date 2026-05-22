"""Gateway service configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class GatewaySettings(BaseAppSettings):
    """Gateway-specific settings."""
    service_name: str = "gateway"
    service_port: int = 8000


@lru_cache()
def get_settings() -> GatewaySettings:
    return GatewaySettings()
