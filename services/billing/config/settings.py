"""Billing service configuration."""

from functools import lru_cache
from shared.config.base_settings import BaseAppSettings


class BillingSettings(BaseAppSettings):
    """Billing specific settings."""

    SERVICE_NAME: str = "billing"
    SERVICE_PORT: int = 8006

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO_MONTHLY: str = ""
    STRIPE_PRICE_PRO_ANNUAL: str = ""

    # Plans
    FREE_KITS_LIMIT: int = 3
    PRO_KITS_LIMIT: int = 100
    PRO_MONTHLY_PRICE: int = 39  # USD


@lru_cache()
def get_billing_settings() -> BillingSettings:
    return BillingSettings()
