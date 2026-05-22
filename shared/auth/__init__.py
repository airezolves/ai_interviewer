"""JWT authentication utilities — used by Gateway and Auth services."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    type: str = "access"


def create_access_token(
    user_id: UUID | str,
    secret_key: str,
    algorithm: str = "HS256",
    expire_minutes: int = 30,
) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    user_id: UUID | str,
    secret_key: str,
    algorithm: str = "HS256",
    expire_days: int = 7,
) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=expire_days)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def verify_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
    expected_type: str = "access",
) -> TokenData | None:
    """Verify and decode a JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(user_id=user_id, type=token_type)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
