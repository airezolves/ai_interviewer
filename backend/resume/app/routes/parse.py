"""Parse routes — upload and parse resumes."""

import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional

from backend.resume.app.parser.pdf_parser import extract_text_from_pdf
from backend.resume.app.parser.docx_parser import extract_text_from_docx
from backend.resume.app.parser.llm_structurer import structure_resume_text
from shared.schemas.resume import ResumeParseResponse, StructuredResume

router = APIRouter()

# In-memory cache for development (replace with Redis in production)
_parse_cache: dict[str, ResumeParseResponse] = {}


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    """Parse a resume from file upload or raw text."""
    raw_text = ""

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

        # Check cache
        file_hash = hashlib.sha256(content).hexdigest()
        if file_hash in _parse_cache:
            cached = _parse_cache[file_hash]
            cached.cached = True
            return cached

        # Extract text
        if extension == "pdf":
            raw_text = extract_text_from_pdf(content)
        elif extension == "docx":
            raw_text = extract_text_from_docx(content)

    elif text:
        raw_text = text
        file_hash = hashlib.sha256(text.encode()).hexdigest()
        if file_hash in _parse_cache:
            cached = _parse_cache[file_hash]
            cached.cached = True
            return cached
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

    response = ResumeParseResponse(
        structured_resume=structured,
        raw_text=raw_text,
        confidence=0.85,
        cached=False,
    )

    # Cache the result
    _parse_cache[file_hash] = response
    return response
