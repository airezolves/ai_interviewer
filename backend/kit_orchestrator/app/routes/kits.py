"""Kit CRUD + the Proceed gate + SSE progress."""

import uuid
import json
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, func

from shared.database import get_database
from shared.database.models import Kit, GenerationJob, FinalAnalysis

router = APIRouter()


class ProceedRequest(BaseModel):
    decision: str  # 'proceed' | 'denied'


def _kit_to_response(kit: Kit, final: FinalAnalysis | None = None) -> dict:
    return {
        "id": str(kit.id),
        "title": kit.title,
        "role_type": kit.role_type,
        "status": kit.status,
        "structured_resume": kit.structured_resume,
        "structured_jd": kit.structured_jd,
        "match_analysis": kit.match_analysis,
        "proceed_decision": kit.proceed_decision,
        "proceed_decided_at": kit.proceed_decided_at.isoformat() if kit.proceed_decided_at else None,
        "final_analysis": (
            {
                "overall_score": float(final.overall_score) if final.overall_score is not None else None,
                "dimension_scores": final.dimension_scores,
                "pros": final.pros,
                "cons": final.cons,
                "recommendation": final.recommendation,
                "role_suitability": final.role_suitability,
                "reasoning": final.reasoning,
            } if final else None
        ),
        "pdf_url": kit.pdf_url,
        "share_token": str(kit.share_token) if kit.share_token else None,
        "created_at": kit.created_at.isoformat() if kit.created_at else None,
    }


@router.get("/kits/{kit_id}")
async def get_kit(kit_id: str, x_user_id: str = Header(...)):
    db = get_database()
    async with db.async_session() as session:
        res = await session.execute(
            select(Kit).where(Kit.id == uuid.UUID(kit_id), Kit.user_id == uuid.UUID(x_user_id))
        )
        kit = res.scalar_one_or_none()
        if not kit:
            raise HTTPException(404, "Kit not found")
        res2 = await session.execute(select(FinalAnalysis).where(FinalAnalysis.kit_id == kit.id))
        final = res2.scalar_one_or_none()
    return _kit_to_response(kit, final)


@router.get("/kits")
async def list_kits(
    x_user_id: str = Header(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    db = get_database()
    offset = (page - 1) * per_page
    async with db.async_session() as session:
        count_res = await session.execute(
            select(func.count(Kit.id)).where(Kit.user_id == uuid.UUID(x_user_id))
        )
        total = count_res.scalar() or 0
        res = await session.execute(
            select(Kit)
            .where(Kit.user_id == uuid.UUID(x_user_id))
            .order_by(Kit.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        kits = res.scalars().all()
    return {
        "kits": [_kit_to_response(k) for k in kits],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.delete("/kits/{kit_id}")
async def delete_kit(kit_id: str, x_user_id: str = Header(...)):
    db = get_database()
    async with db.async_session() as session:
        res = await session.execute(
            select(Kit).where(Kit.id == uuid.UUID(kit_id), Kit.user_id == uuid.UUID(x_user_id))
        )
        kit = res.scalar_one_or_none()
        if not kit:
            raise HTTPException(404, "Kit not found")
        await session.delete(kit)
        await session.commit()
    return {"success": True}


@router.post("/kits/{kit_id}/proceed")
async def set_proceed(kit_id: str, payload: ProceedRequest, x_user_id: str = Header(...)):
    """Recruiter approves or denies the candidate after seeing the match score."""
    if payload.decision not in ("proceed", "denied"):
        raise HTTPException(400, "decision must be 'proceed' or 'denied'")
    db = get_database()
    async with db.async_session() as session:
        res = await session.execute(
            select(Kit).where(Kit.id == uuid.UUID(kit_id), Kit.user_id == uuid.UUID(x_user_id))
        )
        kit = res.scalar_one_or_none()
        if not kit:
            raise HTTPException(404, "Kit not found")
        if kit.status not in ("match_ready", "interviewing", "complete"):
            raise HTTPException(409, f"Kit is in status {kit.status}; cannot set decision")
        kit.proceed_decision = payload.decision
        kit.proceed_decided_at = datetime.now(timezone.utc)
        if payload.decision == "denied":
            kit.status = "denied"
        await session.commit()
    return {"success": True, "decision": payload.decision}


@router.get("/kits/{kit_id}/stream")
async def stream_progress(kit_id: str, x_user_id: str = Header(...)):
    async def event_generator():
        db = get_database()
        last_pct = -1
        while True:
            async with db.async_session() as session:
                res = await session.execute(
                    select(GenerationJob).where(GenerationJob.kit_id == uuid.UUID(kit_id))
                )
                job = res.scalar_one_or_none()
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            if job.progress_pct != last_pct or job.status in ("match_ready", "failed"):
                last_pct = job.progress_pct
                yield f"data: {json.dumps({'status': job.status, 'current_step': job.current_step, 'progress_pct': job.progress_pct})}\n\n"
            if job.status in ("match_ready", "failed"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/shared/{share_token}")
async def get_shared_kit(share_token: str):
    db = get_database()
    async with db.async_session() as session:
        res = await session.execute(select(Kit).where(Kit.share_token == uuid.UUID(share_token)))
        kit = res.scalar_one_or_none()
        if not kit:
            raise HTTPException(404, "Shared kit not found")
        res2 = await session.execute(select(FinalAnalysis).where(FinalAnalysis.kit_id == kit.id))
        final = res2.scalar_one_or_none()
    return _kit_to_response(kit, final)
