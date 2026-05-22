"""Common schemas (pagination, errors, health)."""

from pydantic import BaseModel
from typing import Any


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] | None = None


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
