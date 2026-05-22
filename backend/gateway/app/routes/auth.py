"""Auth routes — proxies to Auth Service."""

from fastapi import APIRouter, Depends
import httpx

from backend.gateway.app.config import get_settings
from backend.gateway.app.middleware.auth import get_current_user
from shared.auth import TokenData
from shared.schemas.auth import (
    UserCreate, LoginRequest, TokenResponse, UserResponse, GoogleOAuthRequest,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    """Register a new user."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/register",
            json=data.model_dump(),
            timeout=10.0,
        )
    if resp.status_code != 200:
        from fastapi import HTTPException
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Login with email + password."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/login",
            json=data.model_dump(),
            timeout=10.0,
        )
    if resp.status_code != 200:
        from fastapi import HTTPException
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.post("/google", response_model=TokenResponse)
async def google_oauth(data: GoogleOAuthRequest):
    """Login/register with Google OAuth."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/oauth/google",
            json=data.model_dump(),
            timeout=10.0,
        )
    if resp.status_code != 200:
        from fastapi import HTTPException
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.get("/me", response_model=UserResponse)
async def get_me(user: TokenData = Depends(get_current_user)):
    """Get current user profile."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.auth_service_url}/users/{user.user_id}",
            timeout=10.0,
        )
    if resp.status_code != 200:
        from fastapi import HTTPException
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()
