"""Kit Orchestrator configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class OrchestratorSettings(BaseAppSettings):
    """Orchestrator-specific settings."""
    service_name: str = "kit_orchestrator"
    service_port: int = 8004


@lru_cache()
def get_settings() -> OrchestratorSettings:
    return OrchestratorSettings()
