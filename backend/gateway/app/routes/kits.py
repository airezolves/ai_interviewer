"""Kit routes — proxies to Kit Orchestrator Service."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import httpx

from backend.gateway.app.config import get_settings
from backend.gateway.app.middleware.auth import get_current_user
from shared.auth import TokenData
from shared.schemas.kit import KitGenerateRequest, KitResponse, KitListResponse, JobStatus

router = APIRouter()


@router.post("/generate", response_model=JobStatus)
async def generate_kit(
    data: KitGenerateRequest,
    user: TokenData = Depends(get_current_user),
):
    """Start kit generation pipeline."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.kit_orchestrator_url}/generate",
            json=data.model_dump(),
            headers={"X-User-ID": user.user_id},
            timeout=30.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.get("/{kit_id}", response_model=KitResponse)
async def get_kit(
    kit_id: str,
    user: TokenData = Depends(get_current_user),
):
    """Get a specific kit by ID."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kit_orchestrator_url}/kits/{kit_id}",
            headers={"X-User-ID": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.get("", response_model=KitListResponse)
async def list_kits(
    page: int = 1,
    per_page: int = 20,
    user: TokenData = Depends(get_current_user),
):
    """List user's kits."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kit_orchestrator_url}/kits",
            params={"page": page, "per_page": per_page},
            headers={"X-User-ID": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@router.delete("/{kit_id}")
async def delete_kit(
    kit_id: str,
    user: TokenData = Depends(get_current_user),
):
    """Delete a kit."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{settings.kit_orchestrator_url}/kits/{kit_id}",
            headers={"X-User-ID": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return {"success": True}


@router.get("/{kit_id}/stream")
async def stream_kit_progress(
    kit_id: str,
    user: TokenData = Depends(get_current_user),
):
    """Stream kit generation progress via SSE."""
    settings = get_settings()

    async def event_generator():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"{settings.kit_orchestrator_url}/kits/{kit_id}/stream",
                headers={"X-User-ID": user.user_id},
                timeout=120.0,
            ) as resp:
                async for line in resp.aiter_lines():
                    yield line + "\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
