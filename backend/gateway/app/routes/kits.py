"""Kit routes — gateway-side proxy + the interactive Q&A endpoints."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.gateway.app.config import get_settings
from backend.gateway.app.middleware.auth import get_current_user
from shared.auth import TokenData

router = APIRouter()


class ProceedRequest(BaseModel):
    decision: str  # 'proceed' | 'denied'


class StartInterviewRequest(BaseModel):
    max_turns: int = 8


class AnswerRequest(BaseModel):
    answer: str


# ─────────────────────────────────────────────────────────────────
#  Generate / list / get / delete  (proxied to orchestrator)
# ─────────────────────────────────────────────────────────────────

@router.post("/generate")
async def generate_kit(
    jd_text: str = Form(...),
    role_type: str = Form(...),
    resume_file: UploadFile | None = File(None),
    resume_text: str | None = Form(None),
    user: TokenData = Depends(get_current_user),
):
    """Start the v2 match pipeline. Resume can be a file (PDF/DOCX) or raw text.
    Structuring is done downstream with the user's active LLM provider."""
    settings = get_settings()
    if not resume_file and not resume_text:
        raise HTTPException(400, "Provide resume_file or resume_text")

    parsed_resume_text = resume_text
    if resume_file:
        content = await resume_file.read()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.resume_service_url}/extract",
                files={"file": (resume_file.filename, content, resume_file.content_type)},
            )
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, f"Extract failed: {resp.text}")
            parsed_resume_text = resp.json().get("raw_text", "")
            if not parsed_resume_text:
                raise HTTPException(400, "Could not extract text from resume file")

    payload = {
        "jd_text": jd_text,
        "role_type": role_type,
        "resume_text": parsed_resume_text,
        "structured_resume": None,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.kit_orchestrator_url}/generate",
            json=payload,
            headers={"X-User-Id": user.user_id},
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.get("/{kit_id}")
async def get_kit(kit_id: str, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kit_orchestrator_url}/kits/{kit_id}",
            headers={"X-User-Id": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.get("")
async def list_kits(page: int = 1, per_page: int = 20, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kit_orchestrator_url}/kits",
            params={"page": page, "per_page": per_page},
            headers={"X-User-Id": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.delete("/{kit_id}")
async def delete_kit(kit_id: str, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{settings.kit_orchestrator_url}/kits/{kit_id}",
            headers={"X-User-Id": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return {"success": True}


@router.get("/{kit_id}/stream")
async def stream_kit_progress(kit_id: str, user: TokenData = Depends(get_current_user)):
    settings = get_settings()

    async def event_generator():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"{settings.kit_orchestrator_url}/kits/{kit_id}/stream",
                headers={"X-User-Id": user.user_id},
                timeout=120.0,
            ) as resp:
                async for line in resp.aiter_lines():
                    yield line + "\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ─────────────────────────────────────────────────────────────────
#  Proceed gate  (proxied to orchestrator)
# ─────────────────────────────────────────────────────────────────

@router.post("/{kit_id}/proceed")
async def set_proceed(kit_id: str, payload: ProceedRequest, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.kit_orchestrator_url}/kits/{kit_id}/proceed",
            json=payload.model_dump(),
            headers={"X-User-Id": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


# ─────────────────────────────────────────────────────────────────
#  Interview Q&A  (proxied to ai_engine)
# ─────────────────────────────────────────────────────────────────

@router.post("/{kit_id}/interview/start")
async def interview_start(kit_id: str, payload: StartInterviewRequest, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.ai_engine_url}/v2/interview/{kit_id}/start",
            json=payload.model_dump(),
            headers={"X-User-Id": user.user_id},
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.get("/{kit_id}/interview")
async def interview_state(kit_id: str, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.ai_engine_url}/v2/interview/{kit_id}",
            headers={"X-User-Id": user.user_id},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.post("/{kit_id}/interview/answer")
async def interview_answer(kit_id: str, payload: AnswerRequest, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.ai_engine_url}/v2/interview/{kit_id}/answer",
            json=payload.model_dump(),
            headers={"X-User-Id": user.user_id},
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.post("/{kit_id}/interview/finalize")
async def interview_finalize(kit_id: str, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.ai_engine_url}/v2/interview/{kit_id}/finalize",
            headers={"X-User-Id": user.user_id},
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()
