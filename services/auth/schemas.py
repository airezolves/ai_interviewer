"""Auth service request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ─── Request Schemas ───

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)


# ─── Response Schemas ───

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    plan: str
    is_verified: bool
    kits_generated_this_month: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    success: bool = True
    user: UserResponse
    tokens: TokenResponse
