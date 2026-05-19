"""Resume Parser service schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ParsedResume(BaseModel):
    """Structured resume data extracted by LLM."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    total_experience_years: float | None = None
    current_role: str | None = None
    skills: list[str] = []
    technical_skills: list[str] = []
    soft_skills: list[str] = []
    experience: list[dict] = []  # [{company, role, duration, highlights}]
    education: list[dict] = []  # [{institution, degree, year}]
    projects: list[dict] = []  # [{name, description, tech_stack}]
    certifications: list[str] = []
    gaps: list[str] = []  # Employment gaps identified
    strengths: list[str] = []
    concerns: list[str] = []


class ResumeParseResponse(BaseModel):
    """Response from resume parsing."""

    id: UUID
    user_id: UUID
    filename: str
    raw_text: str
    structured_data: ParsedResume
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    """Response after uploading and parsing a resume."""

    success: bool = True
    resume_id: UUID
    structured_data: ParsedResume
    raw_text_length: int
