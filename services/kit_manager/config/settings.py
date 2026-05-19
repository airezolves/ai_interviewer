"""Kit Manager service configuration."""

from functools import lru_cache
from shared.config.base_settings import BaseAppSettings


class KitManagerSettings(BaseAppSettings):
    """Kit Manager specific settings."""

    SERVICE_NAME: str = "kit_manager"
    SERVICE_PORT: int = 8004

    # Kit limits
    FREE_KITS_PER_MONTH: int = 3
    PRO_KITS_PER_MONTH: int = 100
    TEAM_KITS_PER_MONTH: int = 500

    # Sharing
    SHARE_LINK_EXPIRY_DAYS: int = 30


@lru_cache()
def get_kit_manager_settings() -> KitManagerSettings:
    return KitManagerSettings()
