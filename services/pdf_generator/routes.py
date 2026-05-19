"""PDF Generator service routes."""

import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse

from shared.schemas.common import APIResponse, HealthResponse
from shared.middleware.error_handler import NotFoundException
from services.pdf_generator.schemas import GeneratePDFRequest, PDFJobStatus
from services.pdf_generator.service import PDFGeneratorService

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(service="pdf_generator")


@router.post("/generate", response_model=APIResponse[PDFJobStatus])
async def generate_pdf(request: GeneratePDFRequest):
    """Generate a PDF from kit data."""
    service = PDFGeneratorService()
    job_id = await service.generate_pdf(
        kit_data=request.kit_data,
        title=request.title,
        candidate_name=request.candidate_name,
    )

    return APIResponse(
        data=PDFJobStatus(
            job_id=job_id,
            status="completed",
            download_url=f"/pdf/{job_id}/download",
        )
    )


@router.get("/{job_id}/download")
async def download_pdf(job_id: str):
    """Download a generated PDF."""
    service = PDFGeneratorService()
    path = service.get_pdf_path(job_id)

    if not path:
        raise NotFoundException("PDF", job_id)

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"interview_kit_{job_id[:8]}.pdf",
    )


@router.get("/{job_id}/status", response_model=APIResponse[PDFJobStatus])
async def get_status(job_id: str):
    """Check PDF generation status."""
    service = PDFGeneratorService()
    path = service.get_pdf_path(job_id)

    status = "completed" if path else "not_found"
    return APIResponse(
        data=PDFJobStatus(
            job_id=job_id,
            status=status,
            download_url=f"/pdf/{job_id}/download" if path else None,
        )
    )
