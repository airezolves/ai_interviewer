"""Parse routes — upload and parse resumes."""

import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from sqlalchemy import select

from backend.resume.app.parser.pdf_parser import extract_text_from_pdf
from backend.resume.app.parser.docx_parser import extract_text_from_docx
from backend.resume.app.parser.llm_structurer import structure_resume_text
from shared.schemas.resume import ResumeParseResponse, StructuredResume
from shared.database import get_database
from shared.database.models import ParsedResume

router = APIRouter()


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),  # Optional: track which user uploaded
):
    """Parse a resume from file upload or raw text.
    
    Uses database caching - if same file/text seen before, returns cached result.
    """
    raw_text = ""
    file_hash = ""
    filename = None
    db = get_database()

    if file:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        extension = file.filename.lower().split(".")[-1]
        if extension not in ("pdf", "docx"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Upload PDF or DOCX.",
            )

        # Read file content
        content = await file.read()

        # Check size (10MB max)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

        # Calculate hash for cache lookup
        file_hash = hashlib.sha256(content).hexdigest()
        filename = file.filename  # Save original filename

        # Check database cache
        async with db.async_session() as session:
            result = await session.execute(
                select(ParsedResume).where(ParsedResume.file_hash == file_hash)
            )
            cached_resume = result.scalar_one_or_none()

        if cached_resume:
            # Return cached result
            return ResumeParseResponse(
                structured_resume=StructuredResume(**cached_resume.structured_data),
                raw_text=cached_resume.raw_text,
                confidence=0.85,
                cached=True,
                parsed_resume_id=str(cached_resume.id),  # Include ID for linking
            )

        # Extract text
        if extension == "pdf":
            raw_text = extract_text_from_pdf(content)
        elif extension == "docx":
            raw_text = extract_text_from_docx(content)

    elif text:
        raw_text = text
        file_hash = hashlib.sha256(text.encode()).hexdigest()

        # Check database cache
        async with db.async_session() as session:
            result = await session.execute(
                select(ParsedResume).where(ParsedResume.file_hash == file_hash)
            )
            cached_resume = result.scalar_one_or_none()

        if cached_resume:
            # Return cached result
            return ResumeParseResponse(
                structured_resume=StructuredResume(**cached_resume.structured_data),
                raw_text=cached_resume.raw_text,
                confidence=0.85,
                cached=True,
                parsed_resume_id=str(cached_resume.id),  # Include ID for linking
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either a file upload or raw text.",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the uploaded file.",
        )

    # Structure via LLM
    structured = await structure_resume_text(raw_text)

    # Save to database cache
    async with db.async_session() as session:
        parsed_resume = ParsedResume(
            user_id=user_id if user_id else None,  # Track which user uploaded (if provided)
            name=filename,  # Save original filename
            file_hash=file_hash,
            raw_text=raw_text,
            structured_data=structured.model_dump(),
        )
        session.add(parsed_resume)
        await session.commit()
        await session.refresh(parsed_resume)  # Get generated ID
        parsed_resume_id = str(parsed_resume.id)

    response = ResumeParseResponse(
        structured_resume=structured,
        raw_text=raw_text,
        confidence=0.85,
        cached=False,
        parsed_resume_id=parsed_resume_id,  # Include ID for linking
    )

    return response