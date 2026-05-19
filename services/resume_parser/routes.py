"""Resume Parser service routes."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.connector import get_db
from shared.schemas.common import APIResponse, HealthResponse
from shared.middleware.error_handler import ServiceException
from services.resume_parser.schemas import ResumeUploadResponse, ParsedResume
from services.resume_parser.service import ResumeParserService
from services.resume_parser.config.settings import get_resume_parser_settings

settings = get_resume_parser_settings()
router = APIRouter(prefix="/resume", tags=["resume"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(service="resume_parser")


@router.post("/parse", response_model=ResumeUploadResponse)
async def parse_resume(
    file: UploadFile = File(...),
    user_id: str = "anonymous",
):
    """Upload and parse a resume file."""
    # Validate file type
    extension = Path(file.filename or "").suffix.lower()
    if extension not in (".pdf", ".docx", ".doc"):
        raise ServiceException(
            f"Unsupported file format '{extension}'. Use PDF or DOCX.",
            status_code=400,
        )

    # Validate file size
    file_bytes = await file.read()
    max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise ServiceException(
            f"File too large. Maximum size is {settings.MAX_RESUME_SIZE_MB}MB.",
            status_code=400,
        )

    # Parse the resume
    parser_service = ResumeParserService()
    raw_text, structured_data = await parser_service.parse_resume(file_bytes, file.filename or "resume.pdf")

    resume_id = uuid.uuid4()

    return ResumeUploadResponse(
        resume_id=resume_id,
        structured_data=structured_data,
        raw_text_length=len(raw_text),
    )


@router.post("/parse-text", response_model=APIResponse[ParsedResume])
async def parse_resume_text(body: dict):
    """Parse resume from pasted text (no file upload)."""
    raw_text = body.get("text", "")
    if not raw_text or len(raw_text) < 50:
        raise ServiceException("Resume text is too short", status_code=400)

    parser_service = ResumeParserService()
    structured_data = await parser_service._structure_with_llm(raw_text)

    return APIResponse(data=structured_data)
