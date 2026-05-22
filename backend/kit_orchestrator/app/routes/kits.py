"""Kit CRUD routes and SSE streaming."""

import uuid
import json
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
import asyncio

from shared.database import get_database
from shared.database.models import Kit, GenerationJob
from shared.schemas.kit import KitResponse, KitListResponse, JobStatus

router = APIRouter()


@router.get("/kits/{kit_id}")
async def get_kit(kit_id: str, x_user_id: str = Header(...)):
    """Get a specific kit."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(Kit).where(Kit.id == uuid.UUID(kit_id), Kit.user_id == uuid.UUID(x_user_id))
        )
        kit = result.scalar_one_or_none()

    if not kit:
        raise HTTPException(status_code=404, detail="Kit not found")

    return _kit_to_response(kit)


@router.get("/kits")
async def list_kits(
    x_user_id: str = Header(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List user's kits with pagination."""
    db = get_database()
    offset = (page - 1) * per_page

    async with db.async_session() as session:
        # Count total
        count_result = await session.execute(
            select(func.count(Kit.id)).where(Kit.user_id == uuid.UUID(x_user_id))
        )
        total = count_result.scalar() or 0

        # Fetch page
        result = await session.execute(
            select(Kit)
            .where(Kit.user_id == uuid.UUID(x_user_id))
            .order_by(Kit.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        kits = result.scalars().all()

    return KitListResponse(
        kits=[_kit_to_response(k) for k in kits],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.delete("/kits/{kit_id}")
async def delete_kit(kit_id: str, x_user_id: str = Header(...)):
    """Delete a kit."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(Kit).where(Kit.id == uuid.UUID(kit_id), Kit.user_id == uuid.UUID(x_user_id))
        )
        kit = result.scalar_one_or_none()
        if not kit:
            raise HTTPException(status_code=404, detail="Kit not found")
        await session.delete(kit)
        await session.commit()

    return {"success": True}


@router.get("/kits/{kit_id}/stream")
async def stream_progress(kit_id: str, x_user_id: str = Header(...)):
    """Stream kit generation progress via SSE."""

    async def event_generator():
        db = get_database()
        last_pct = -1

        while True:
            async with db.async_session() as session:
                result = await session.execute(
                    select(GenerationJob).where(GenerationJob.kit_id == uuid.UUID(kit_id))
                )
                job = result.scalar_one_or_none()

            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            if job.progress_pct != last_pct:
                last_pct = job.progress_pct
                event_data = {
                    "status": job.status,
                    "current_step": job.current_step,
                    "progress_pct": job.progress_pct,
                }
                yield f"data: {json.dumps(event_data)}\n\n"

            if job.status in ("complete", "partial", "failed"):
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/shared/{share_token}")
async def get_shared_kit(share_token: str):
    """Get a kit by share token (public)."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(Kit).where(Kit.share_token == uuid.UUID(share_token))
        )
        kit = result.scalar_one_or_none()

    if not kit:
        raise HTTPException(status_code=404, detail="Shared kit not found")
    return _kit_to_response(kit)


def _kit_to_response(kit: Kit) -> dict:
    """Convert Kit model to response dict."""
    return {
        "id": str(kit.id),
        "title": kit.title,
        "role_type": kit.role_type,
        "status": kit.status,
        "match_analysis": kit.match_analysis,
        "questions": kit.questions,
        "practical_test": kit.practical_test,
        "rubric": kit.rubric,
        "red_flags": kit.red_flags,
        "flow_guide": kit.flow_guide,
        "pdf_url": kit.pdf_url,
        "share_token": str(kit.share_token) if kit.share_token else None,
        "created_at": kit.created_at.isoformat() if kit.created_at else None,
    }
