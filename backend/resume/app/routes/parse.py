"""Resume parsing — file upload to raw text. LLM-based structuring is handled
by the ai_engine service using the per-user LLM provider."""

import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.resume.app.parser.pdf_parser import extract_text_from_pdf
from backend.resume.app.parser.docx_parser import extract_text_from_docx

router = APIRouter()


@router.post("/extract")
async def extract_text(file: UploadFile = File(...)):
    """Extract raw text from a PDF or DOCX upload."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    extension = file.filename.lower().split(".")[-1]
    if extension not in ("pdf", "docx"):
        raise HTTPException(400, "Unsupported file type. Upload PDF or DOCX.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 10MB.")

    raw_text = extract_text_from_pdf(content) if extension == "pdf" else extract_text_from_docx(content)
    if not raw_text.strip():
        raise HTTPException(422, "Could not extract text from the uploaded file.")

    return {"raw_text": raw_text, "file_hash": hashlib.sha256(content).hexdigest()}
