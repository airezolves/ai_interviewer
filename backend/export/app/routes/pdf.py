"""PDF generation routes."""

import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy import select

from backend.export.app.config import get_settings
from backend.export.app.services.pdf_renderer import render_kit_pdf
from shared.database import get_database
from shared.database.models import Kit

router = APIRouter()


@router.post("/pdf/{kit_id}")
async def generate_pdf(kit_id: str, x_user_id: str = Header(...)):
    """Generate a PDF for a completed kit."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(Kit).where(Kit.id == uuid.UUID(kit_id), Kit.user_id == uuid.UUID(x_user_id))
        )
        kit = result.scalar_one_or_none()

    if not kit:
        raise HTTPException(status_code=404, detail="Kit not found")
    if kit.status not in ("complete", "partial"):
        raise HTTPException(status_code=400, detail="Kit generation not complete yet")

    # Generate PDF
    settings = get_settings()
    output_dir = Path(settings.storage_local_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_filename = f"kit_{kit_id}.pdf"
    pdf_path = output_dir / pdf_filename

    await render_kit_pdf(kit, pdf_path)

    # Update kit with PDF URL
    async with db.async_session() as session:
        result = await session.execute(select(Kit).where(Kit.id == uuid.UUID(kit_id)))
        kit_obj = result.scalar_one_or_none()
        if kit_obj:
            kit_obj.pdf_url = str(pdf_path)
            await session.commit()

    return {"pdf_url": f"/download/{kit_id}", "filename": pdf_filename}


@router.get("/download/{kit_id}")
async def download_pdf(kit_id: str):
    """Download a generated PDF."""
    settings = get_settings()
    pdf_path = Path(settings.storage_local_path) / f"kit_{kit_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found. Generate it first.")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"interview_kit_{kit_id}.pdf",
    )
