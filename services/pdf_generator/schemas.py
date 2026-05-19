"""PDF Generator service schemas."""

from uuid import UUID
from pydantic import BaseModel


class GeneratePDFRequest(BaseModel):
    """Request to generate a PDF from kit data."""
    kit_id: UUID
    kit_data: dict  # Full kit sections
    title: str
    candidate_name: str | None = None
    role_type: str


class PDFJobStatus(BaseModel):
    job_id: str
    status: str  # pending, generating, completed, failed
    download_url: str | None = None
