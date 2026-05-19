"""Auth service API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.connector import get_db
from shared.schemas.common import APIResponse, HealthResponse
from shared.utils.security import decode_token
from shared.middleware.error_handler import UnauthorizedException
from services.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    UpdateProfileRequest,
    AuthResponse,
    UserResponse,
    TokenResponse,
)
from services.auth.service import AuthService
from services.auth.config.settings import get_auth_settings

settings = get_auth_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user_id(token: str = None) -> UUID:
    """Extract user_id from JWT token. Simplified - gateway handles full validation."""
    if not token:
        raise UnauthorizedException()
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException("Invalid token")
    return UUID(payload["sub"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(service="auth")


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(request)


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(request)


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")

    user_id = UUID(payload["sub"])
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)

    # Re-generate tokens
    from shared.utils.security import create_access_token, create_refresh_token
    token_data = {"sub": str(user.id), "email": user.email, "plan": user.plan}
    tokens = TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return APIResponse(data=tokens)


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_profile(user_id: UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    return APIResponse(data=user)


@router.put("/me", response_model=APIResponse[UserResponse])
async def update_profile(
    request: UpdateProfileRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.update_profile(user_id, name=request.name)
    return APIResponse(data=user)


@router.get("/validate-token")
async def validate_token(user_id: UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Internal endpoint for gateway to validate tokens."""
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    return {"valid": True, "user_id": str(user.id), "email": user.email, "plan": user.plan}
