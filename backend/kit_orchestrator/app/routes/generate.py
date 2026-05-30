"""Generate route — kicks off the v2 match pipeline."""

import asyncio
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Header

from backend.kit_orchestrator.app.config import get_settings
from backend.kit_orchestrator.app.pipeline.controller import run_match_pipeline
from shared.database import get_database
from shared.database.models import Kit, GenerationJob
from shared.schemas.kit import KitGenerateRequest, JobStatus

router = APIRouter()


@router.post("/generate", response_model=JobStatus)
async def generate_kit(
    data: KitGenerateRequest,
    x_user_id: str = Header(...),
):
    """Create a kit record and start the v2 match pipeline."""
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.auth_service_url}/users/{x_user_id}/can-generate",
            timeout=5.0,
        )
        if resp.status_code == 200:
            r = resp.json()
            if not r.get("allowed", False):
                raise HTTPException(status_code=403, detail=r.get("reason", "Limit reached"))

    db = get_database()
    kit_id = uuid.uuid4()
    job_id = uuid.uuid4()

    async with db.async_session() as session:
        kit = Kit(
            id=kit_id,
            user_id=uuid.UUID(x_user_id),
            role_type=data.role_type.value,
            status="matching",
            jd_text=data.jd_text,
            resume_text=data.resume_text,
        )
        session.add(kit)
        job = GenerationJob(
            id=job_id,
            kit_id=kit_id,
            user_id=uuid.UUID(x_user_id),
            status="matching",
            progress_pct=0,
        )
        session.add(job)
        await session.commit()

    asyncio.create_task(
        run_match_pipeline(
            kit_id=kit_id,
            job_id=job_id,
            user_id=x_user_id,
            jd_text=data.jd_text,
            resume_text=data.resume_text,
            role_type=data.role_type.value,
            structured_resume=data.structured_resume,
        )
    )

    return JobStatus(
        job_id=job_id,
        kit_id=kit_id,
        status="matching",
        current_step="queued",
        progress_pct=0,
    )
