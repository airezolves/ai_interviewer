"""Gateway service configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class GatewaySettings(BaseAppSettings):
    """Gateway-specific settings."""
    service_name: str = "gateway"
    service_port: int = 8000

    # Rate limiting
    rate_limit_free_requests_per_minute: int = 60
    rate_limit_pro_requests_per_minute: int = 300

    # Service URLs (for proxying)
    auth_service_url: str = "http://localhost:8001"
    resume_service_url: str = "http://localhost:8002"
    kit_orchestrator_url: str = "http://localhost:8004"
    export_service_url: str = "http://localhost:8005"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> GatewaySettings:
    return GatewaySettings()
