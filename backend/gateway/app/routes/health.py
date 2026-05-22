"""Health check routes."""

from fastapi import APIRouter
from shared.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(service="gateway", status="healthy")
