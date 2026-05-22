"""Auth dependency — verifies JWT from Authorization header."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from shared.auth import verify_token, TokenData
from backend.gateway.app.config import get_settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Verify JWT and extract user data."""
    settings = get_settings()
    token_data = verify_token(
        token=credentials.credentials,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> TokenData | None:
    """Optionally verify JWT (for public endpoints that behave differently when authenticated)."""
    if credentials is None:
        return None
    settings = get_settings()
    return verify_token(
        token=credentials.credentials,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
