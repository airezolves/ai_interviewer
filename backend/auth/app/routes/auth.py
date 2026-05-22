"""Auth routes — register, login, OAuth."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from backend.auth.app.config import get_settings
from backend.auth.app.services.password import hash_password, verify_password
from shared.auth import create_access_token, create_refresh_token
from shared.database import get_database
from shared.database.models import User
from shared.schemas.auth import UserCreate, LoginRequest, TokenResponse, GoogleOAuthRequest

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    """Register a new user with email + password."""
    db = get_database()
    async with db.async_session() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == data.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        # Create user
        user = User(
            email=data.email,
            name=data.name,
            password_hash=hash_password(data.password),
            auth_provider="email",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Generate tokens
    settings = get_settings()
    access_token = create_access_token(
        user_id=user.id,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_access_token_expire_minutes,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_days=settings.jwt_refresh_token_expire_days,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Login with email + password."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    settings = get_settings()
    access_token = create_access_token(
        user_id=user.id,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_access_token_expire_minutes,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_days=settings.jwt_refresh_token_expire_days,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/oauth/google", response_model=TokenResponse)
async def google_oauth(data: GoogleOAuthRequest):
    """Login/register with Google OAuth code exchange."""
    settings = get_settings()

    # Exchange code for user info
    import httpx
    async with httpx.AsyncClient() as client:
        # Exchange authorization code for tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": data.code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": data.redirect_uri or settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google OAuth code")

        google_tokens = token_resp.json()

        # Get user info
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google user info")

        google_user = userinfo_resp.json()

    # Find or create user
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(User).where(User.email == google_user["email"])
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=google_user["email"],
                name=google_user.get("name", ""),
                auth_provider="google",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

    # Generate tokens
    access_token = create_access_token(
        user_id=user.id,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_access_token_expire_minutes,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_days=settings.jwt_refresh_token_expire_days,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
