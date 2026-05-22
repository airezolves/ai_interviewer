"""Auth service configuration."""

from functools import lru_cache
from shared.config import BaseAppSettings


class AuthSettings(BaseAppSettings):
    """Auth-specific settings."""
    service_name: str = "auth"
    service_port: int = 8001
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/auth/callback/google"


@lru_cache()
def get_settings() -> AuthSettings:
    return AuthSettings()
