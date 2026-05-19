"""Gateway service configuration."""

from functools import lru_cache
from shared.config.base_settings import BaseAppSettings


class GatewaySettings(BaseAppSettings):
    """Gateway specific settings."""

    SERVICE_NAME: str = "gateway"
    SERVICE_PORT: int = 8000

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60


@lru_cache()
def get_gateway_settings() -> GatewaySettings:
    return GatewaySettings()
