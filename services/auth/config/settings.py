"""Auth service configuration."""

from functools import lru_cache
from shared.config.base_settings import BaseAppSettings


class AuthSettings(BaseAppSettings):
    """Auth-service-specific settings."""

    SERVICE_NAME: str = "auth"
    SERVICE_PORT: int = 8001

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/oauth/google/callback"

    # Rate limiting
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15


@lru_cache()
def get_auth_settings() -> AuthSettings:
    return AuthSettings()
