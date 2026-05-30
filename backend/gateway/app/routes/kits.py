"""Kit routes — proxies to Kit Orchestrator Service."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
import httpx

from backend.gateway.app.config import get_settings
from backend.gateway.app.middleware.auth import get_current_user
from shared.auth import TokenData
from shared.schemas.kit import KitGenerateRequest, KitResponse, KitListResponse, JobStatus

router = APIRouter()


@router.post("/generate", response_model=JobStatus)
async def generate_kit(
    jd_text: str = Form(...),
    role_type: str = Form(...),
    resume_file: UploadFile | None = File(None),
    resume_text: str | None = Form(None),
    user: TokenData = Depends(get_current_user),
):
    """
    Start kit generation pipeline.
    Accepts either resume_file (PDF/DOCX) or resume_text (plain text).
    If file is provided, it will be parsed automatically.
    """
    settings = get_settings()
    
    # Validate that at least one resume input is provided
    if not resume_file and not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Either resume_file or resume_text must be provided"
        )
    
    # If file is uploaded, parse it first
    parsed_resume_text = resume_text
    structured_resume_data = None
    parsed_resume_id = None
    
    if resume_file:
        try:
            # Read file content
            file_content = await resume_file.read()
            
            # Call resume service to parse the file (extract + structure in one call)
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": (resume_file.filename, file_content, resume_file.content_type)}
                data = {"user_id": user.user_id}  # Pass user_id to track who uploaded
                resp = await client.post(
                    f"{settings.resume_service_url}/parse",
                    files=files,
                    data=data,
                )
                
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"Resume parsing failed: {resp.text}"
                    )
                
                parse_result = resp.json()
                parsed_resume_text = parse_result.get("raw_text", "")
                structured_resume_data = parse_result.get("structured_resume")
                parsed_resume_id = parse_result.get("parsed_resume_id")  # Get ID for linking
                
                if not parsed_resume_text:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not extract text from resume file"
                    )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse resume file: {str(e)}"
            )
    
    # Create the request payload for orchestrator
    kit_data = KitGenerateRequest(
        jd_text=jd_text,
        resume_text=parsed_resume_text,
        role_type=role_type,
        structured_resume=structured_resume_data,  # Send pre-structured resume if available
        parsed_resume_id=parsed_resume_id,  # Link to parsed resume for tracking
    )
    
    # Send to orchestrator
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.kit_orchestrator_url}/generate",
                json=kit_data.model_dump(),
                headers={"X-User-ID": user.user_id},
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.json())
        return resp.json()
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid request data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start kit generation: {str(e)}"
        )


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
