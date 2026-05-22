"""Resume-related schemas."""

from pydantic import BaseModel


class Project(BaseModel):
    name: str
    description: str
    technologies: list[str] = []


class Education(BaseModel):
    degree: str
    institution: str
    year: str | None = None
    field: str | None = None


class Employment(BaseModel):
    company: str
    role: str
    duration: str
    responsibilities: list[str] = []


class StructuredResume(BaseModel):
    skills: list[str] = []
    experience_level: str = "mid"  # junior, mid, senior
    years_of_experience: float = 0
    tech_stack: list[str] = []
    projects: list[Project] = []
    education: list[Education] = []
    employment_timeline: list[Employment] = []
    gaps: list[str] = []
    summary: str = ""
    raw_text: str = ""


class ResumeParseRequest(BaseModel):
    text: str | None = None  # Raw text input (alternative to file upload)


class ResumeParseResponse(BaseModel):
    structured_resume: StructuredResume
    raw_text: str
    confidence: float = 0.0
    cached: bool = False
