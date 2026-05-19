"""Common response schemas used across services."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: T | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: str | None = None
    status_code: int = 400


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    success: bool = True
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    """Service health check response."""
    service: str
    status: str = "healthy"
    version: str = "0.1.0"


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str  # user_id
    exp: int
    type: str  # "access" or "refresh"


class UserContext(BaseModel):
    """User context passed between services."""
    user_id: UUID
    email: str
    plan: str = "free"
