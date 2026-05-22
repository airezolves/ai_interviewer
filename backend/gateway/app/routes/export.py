"""Export routes — proxies to Export Service."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import httpx

from backend.gateway.app.config import get_settings
from backend.gateway.app.middleware.auth import get_current_user, get_optional_user
from shared.auth import TokenData

router = APIRouter()


@router.post("/pdf/{kit_id}")
async def generate_pdf(
    kit_id: str,
    user: TokenData = Depends(get_current_user),
):
    """Generate PDF for a kit."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.export_service_url}/pdf/{kit_id}",
            headers={"X-User-ID": user.user_id},
            timeout=30.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.get("/download/{export_id}")
async def download_pdf(export_id: str):
    """Download a generated PDF."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.export_service_url}/download/{export_id}",
            timeout=30.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return StreamingResponse(
        iter([resp.content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=interview_kit_{export_id}.pdf"},
    )


@router.get("/shared/{share_token}")
async def get_shared_kit(share_token: str):
    """Get a shared kit (public, no auth required)."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kit_orchestrator_url}/shared/{share_token}",
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()
