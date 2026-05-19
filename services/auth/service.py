"""Auth service business logic."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from shared.middleware.error_handler import ServiceException, NotFoundException, UnauthorizedException
from services.auth.models import User
from services.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
    AuthResponse,
)
from services.auth.config.settings import get_auth_settings

settings = get_auth_settings()


class AuthService:
    """Handles user authentication and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: RegisterRequest) -> AuthResponse:
        """Register a new user."""
        # Check if user exists
        existing = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            raise ServiceException("Email already registered", status_code=409)

        # Create user
        user = User(
            email=request.email,
            name=request.name,
            password_hash=hash_password(request.password),
            plan="free",
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        # Generate tokens
        tokens = self._generate_tokens(user)

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def login(self, request: LoginRequest) -> AuthResponse:
        """Authenticate user with email/password."""
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(request.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

        tokens = self._generate_tokens(user)

        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def get_user_by_id(self, user_id: UUID) -> UserResponse:
        """Get user profile by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User", str(user_id))

        return UserResponse.model_validate(user)

    async def update_profile(self, user_id: UUID, name: str | None = None) -> UserResponse:
        """Update user profile."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User", str(user_id))

        if name:
            user.name = name

        await self.db.flush()
        await self.db.refresh(user)

        return UserResponse.model_validate(user)

    async def increment_usage(self, user_id: UUID) -> bool:
        """Increment kit generation count. Returns False if limit reached."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Check plan limits
        limits = {"free": 3, "pro": 100, "team": 500}
        max_kits = limits.get(user.plan, 3)

        if user.kits_generated_this_month >= max_kits:
            return False

        user.kits_generated_this_month += 1
        await self.db.flush()
        return True

    def _generate_tokens(self, user: User) -> TokenResponse:
        """Generate access and refresh tokens for a user."""
        token_data = {"sub": str(user.id), "email": user.email, "plan": user.plan}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
