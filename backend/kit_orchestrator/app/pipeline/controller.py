"""Pipeline Controller — orchestrates the full kit generation flow."""

import asyncio
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from backend.kit_orchestrator.app.config import get_settings
from shared.database import get_database
from shared.database.models import Kit, GenerationJob


async def run_pipeline(
    kit_id: uuid.UUID,
    job_id: uuid.UUID,
    user_id: str,
    jd_text: str,
    resume_text: str | None,
    role_type: str,
):
    """Execute the full kit generation pipeline.
    
    Flow:
    1. Parse resume (Resume Service) + Analyze JD (AI Engine) — PARALLEL
    2. Match score (AI Engine)
    3. Generate all sections — PARALLEL (questions, test, rubric, flags, flow)
    4. Assemble kit + store in DB
    """
    settings = get_settings()
    db = get_database()

    async def update_job(status: str, step: str, pct: int, error: str | None = None):
        async with db.async_session() as session:
            result = await session.execute(select(GenerationJob).where(GenerationJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.status = status
                job.current_step = step
                job.progress_pct = pct
                if error:
                    job.error_message = error
                if status == "generating" and not job.started_at:
                    job.started_at = datetime.now(timezone.utc)
                if status in ("complete", "partial", "failed"):
                    job.completed_at = datetime.now(timezone.utc)
                await session.commit()

    try:
        await update_job("generating", "parsing", 5)

        async with httpx.AsyncClient(timeout=60.0) as client:
            # ─── Phase 1: Parse resume + Analyze JD (parallel) ─────────
            await update_job("generating", "parsing_resume_and_jd", 10)

            parse_coro = _parse_resume(client, settings, resume_text)
            jd_coro = _analyze_jd(client, settings, jd_text)
            structured_resume, structured_jd = await asyncio.gather(parse_coro, jd_coro)

            await update_job("generating", "match_analysis", 25)

            # ─── Phase 2: Match score ──────────────────────────────────
            match_analysis = await _match_score(client, settings, structured_resume, structured_jd, role_type)

            await update_job("generating", "generating_kit_sections", 35)

            # ─── Phase 3: Generate all sections (parallel) ─────────────
            context = {
                "structured_resume": structured_resume,
                "structured_jd": structured_jd,
                "match_analysis": match_analysis,
                "role_type": role_type,
            }

            questions_coro = _generate(client, settings, "/generate-questions", context)
            test_coro = _generate(client, settings, "/generate-test", context)
            rubric_coro = _generate(client, settings, "/generate-rubric", context)
            flags_coro = _generate(client, settings, "/generate-red-flags", context)
            flow_coro = _generate(client, settings, "/generate-flow", context)

            results = await asyncio.gather(
                questions_coro, test_coro, rubric_coro, flags_coro, flow_coro,
                return_exceptions=True,
            )

            questions = results[0] if not isinstance(results[0], Exception) else None
            practical_test = results[1] if not isinstance(results[1], Exception) else None
            rubric = results[2] if not isinstance(results[2], Exception) else None
            red_flags = results[3] if not isinstance(results[3], Exception) else None
            flow_guide = results[4] if not isinstance(results[4], Exception) else None

            await update_job("generating", "assembling", 85)

        # ─── Phase 4: Assemble and store ───────────────────────────
        async with db.async_session() as session:
            result = await session.execute(select(Kit).where(Kit.id == kit_id))
            kit = result.scalar_one_or_none()
            if kit:
                kit.structured_resume = structured_resume
                kit.structured_jd = structured_jd
                kit.match_analysis = match_analysis
                kit.questions = questions
                kit.practical_test = practical_test
                kit.rubric = rubric
                kit.red_flags = red_flags
                kit.flow_guide = flow_guide
                kit.title = _generate_title(structured_jd, role_type)

                # Determine final status
                all_sections = [questions, practical_test, rubric, red_flags, flow_guide]
                if all(s is not None for s in all_sections):
                    kit.status = "complete"
                elif any(s is not None for s in all_sections):
                    kit.status = "partial"
                else:
                    kit.status = "failed"

                await session.commit()

        # Increment usage
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.auth_service_url}/users/{user_id}/increment-usage",
                timeout=5.0,
            )

        final_status = "complete" if all(s is not None for s in [questions, practical_test, rubric, red_flags, flow_guide]) else "partial"
        await update_job(final_status, "done", 100)

    except Exception as e:
        await update_job("failed", "error", 0, error=str(e))


async def _parse_resume(client: httpx.AsyncClient, settings, resume_text: str | None) -> dict:
    """Call Resume Service to parse resume."""
    if not resume_text:
        return {}
    resp = await client.post(
        f"{settings.resume_service_url}/parse",
        data={"text": resume_text},
        timeout=30.0,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get("structured_resume", {})
    return {}


async def _analyze_jd(client: httpx.AsyncClient, settings, jd_text: str) -> dict:
    """Call AI Engine to analyze JD."""
    resp = await client.post(
        f"{settings.ai_engine_url}/analyze-jd",
        json={"jd_text": jd_text},
        timeout=30.0,
    )
    if resp.status_code == 200:
        return resp.json()
    return {}


async def _match_score(client: httpx.AsyncClient, settings, resume: dict, jd: dict, role_type: str) -> dict:
    """Call AI Engine for match scoring."""
    resp = await client.post(
        f"{settings.ai_engine_url}/match-score",
        json={"structured_resume": resume, "structured_jd": jd, "role_type": role_type},
        timeout=30.0,
    )
    if resp.status_code == 200:
        return resp.json()
    return {"overall_match_score": 0, "skill_matches": [], "skill_gaps": []}


async def _generate(client: httpx.AsyncClient, settings, endpoint: str, context: dict) -> dict | list | None:
    """Call AI Engine generation endpoint."""
    resp = await client.post(
        f"{settings.ai_engine_url}{endpoint}",
        json=context,
        timeout=60.0,
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def _generate_title(structured_jd: dict, role_type: str) -> str:
    """Generate a kit title from JD info."""
    company = structured_jd.get("company_info", "")
    role = role_type.replace("_", " ").title()
    if company:
        return f"{role} Interview Kit — {company[:50]}"
    return f"{role} Interview Kit"
