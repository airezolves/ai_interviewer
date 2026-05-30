"""V2 pipeline — parse JD/resume in parallel, then run the Match Agent.

Stops at status='match_ready' so the recruiter can hit the Proceed gate.
The interview turns and analysis are driven by separate ai_engine endpoints.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from backend.kit_orchestrator.app.config import get_settings
from shared.database import get_database
from shared.database.models import Kit, GenerationJob

logger = logging.getLogger(__name__)


async def _update_job(job_id: uuid.UUID, status: str, step: str, pct: int, error: str | None = None):
    db = get_database()
    async with db.async_session() as session:
        res = await session.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        job = res.scalar_one_or_none()
        if not job:
            return
        job.status = status
        job.current_step = step
        job.progress_pct = pct
        if error:
            job.error_message = error
        if status == "matching" and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        if status in ("match_ready", "failed"):
            job.completed_at = datetime.now(timezone.utc)
        await session.commit()


async def _structure_resume(client: httpx.AsyncClient, settings, x_user_id: str, raw_text: str) -> dict | None:
    if not raw_text:
        return None
    try:
        resp = await client.post(
            f"{settings.ai_engine_url}/v2/structure-resume",
            json={"raw_text": raw_text},
            headers={"X-User-Id": x_user_id},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.exception("structure-resume failed: %s", e)
        return None


async def _analyze_jd(client: httpx.AsyncClient, settings, x_user_id: str, jd_text: str) -> dict | None:
    try:
        resp = await client.post(
            f"{settings.ai_engine_url}/v2/analyze-jd",
            json={"jd_text": jd_text},
            headers={"X-User-Id": x_user_id},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.exception("analyze-jd failed: %s", e)
        return None


async def _match(client: httpx.AsyncClient, settings, x_user_id: str, resume: dict, jd: dict, role_type: str) -> dict | None:
    try:
        resp = await client.post(
            f"{settings.ai_engine_url}/v2/match",
            json={"structured_resume": resume, "structured_jd": jd, "role_type": role_type},
            headers={"X-User-Id": x_user_id},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.exception("match failed: %s", e)
        return None


def _generate_title(structured_jd: dict | None, role_type: str) -> str:
    company = (structured_jd or {}).get("company_info") or ""
    role = role_type.replace("_", " ").title()
    if company:
        return f"{role} Interview Kit — {company[:50]}"
    return f"{role} Interview Kit"


async def run_match_pipeline(
    kit_id: uuid.UUID,
    job_id: uuid.UUID,
    user_id: str,
    jd_text: str,
    resume_text: str | None,
    role_type: str,
    structured_resume: dict | None = None,
):
    settings = get_settings()
    db = get_database()
    try:
        await _update_job(job_id, "matching", "structuring", 10)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resume_coro = (
                asyncio.sleep(0)  # already structured
                if structured_resume
                else _structure_resume(client, settings, user_id, resume_text or "")
            )
            jd_coro = _analyze_jd(client, settings, user_id, jd_text)
            resume_res, jd_res = await asyncio.gather(resume_coro, jd_coro)
            sr = structured_resume if structured_resume else resume_res
            sj = jd_res

            await _update_job(job_id, "matching", "match_score", 60)

            if not sr or not sj:
                await _update_job(job_id, "failed", "structuring_failed", 0, error="parse failed")
                async with db.async_session() as session:
                    res = await session.execute(select(Kit).where(Kit.id == kit_id))
                    kit = res.scalar_one_or_none()
                    if kit:
                        kit.status = "failed"
                        kit.structured_resume = sr
                        kit.structured_jd = sj
                        await session.commit()
                return

            match = await _match(client, settings, user_id, sr, sj, role_type)

        async with db.async_session() as session:
            res = await session.execute(select(Kit).where(Kit.id == kit_id))
            kit = res.scalar_one_or_none()
            if not kit:
                return
            kit.structured_resume = sr
            kit.structured_jd = sj
            kit.match_analysis = match
            kit.title = _generate_title(sj, role_type)
            kit.status = "match_ready" if match else "failed"
            await session.commit()

        # Increment usage
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{settings.auth_service_url}/users/{user_id}/increment-usage",
                    timeout=5.0,
                )
            except Exception:
                pass

        await _update_job(job_id, "match_ready" if match else "failed", "done", 100)

    except Exception as e:
        logger.exception("Pipeline failed")
        await _update_job(job_id, "failed", "error", 0, error=str(e))
        async with db.async_session() as session:
            res = await session.execute(select(Kit).where(Kit.id == kit_id))
            kit = res.scalar_one_or_none()
            if kit:
                kit.status = "failed"
                await session.commit()
