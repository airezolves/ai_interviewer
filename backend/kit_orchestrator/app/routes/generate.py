"""Generate route — triggers the kit generation pipeline."""

import asyncio
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header

from backend.kit_orchestrator.app.config import get_settings
from backend.kit_orchestrator.app.pipeline.controller import run_pipeline
from shared.database import get_database
from shared.database.models import Kit, GenerationJob
from shared.schemas.kit import KitGenerateRequest, JobStatus

router = APIRouter()


@router.post("/generate", response_model=JobStatus)
async def generate_kit(
    data: KitGenerateRequest,
    x_user_id: str = Header(...),
):
    """Start kit generation. Returns job_id for tracking progress."""
    settings = get_settings()

    # Check usage limits (call auth service)
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.auth_service_url}/users/{x_user_id}/can-generate",
            timeout=5.0,
        )
        if resp.status_code == 200:
            result = resp.json()
            if not result.get("allowed", False):
                raise HTTPException(
                    status_code=403,
                    detail=result.get("reason", "Kit generation limit reached"),
                )

    # Create kit record
    db = get_database()
    kit_id = uuid.uuid4()
    job_id = uuid.uuid4()

    async with db.async_session() as session:
        kit = Kit(
            id=kit_id,
            user_id=uuid.UUID(x_user_id),
            role_type=data.role_type.value,
            status="pending",
            jd_text=data.jd_text,
            resume_text=data.resume_text,
        )
        session.add(kit)

        job = GenerationJob(
            id=job_id,
            kit_id=kit_id,
            user_id=uuid.UUID(x_user_id),
            status="pending",
            progress_pct=0,
        )
        session.add(job)
        await session.commit()

    # Run pipeline in background
    asyncio.create_task(
        run_pipeline(
            kit_id=kit_id,
            job_id=job_id,
            user_id=x_user_id,
            jd_text=data.jd_text,
            resume_text=data.resume_text,
            role_type=data.role_type.value,
            structured_resume=data.structured_resume,  # Pass pre-structured resume
        )
    )

    return JobStatus(
        job_id=job_id,
        kit_id=kit_id,
        status="pending",
        current_step="queued",
        progress_pct=0,
    )
