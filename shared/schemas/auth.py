"""Auth-related schemas."""

from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: str
    name: str | None = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    auth_provider: str = "email"
    plan: str = "free"
    kits_generated_this_month: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int
    type: str = "access"  # access or refresh


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleOAuthRequest(BaseModel):
    code: str
    redirect_uri: str | None = None
