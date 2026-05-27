"""Resume-related schemas with structured Pydantic models for LLM parsing."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Project(BaseModel):
    """A project mentioned in the resume."""
    
    name: str = Field(
        description="Project name or title"
    )
    description: str = Field(
        description="Brief description of what the project does or achieved"
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies, frameworks, or tools used in the project"
    )


class Education(BaseModel):
    """Educational qualification."""
    
    degree: str = Field(
        description="Degree or certification name (e.g., 'Bachelor of Science', 'MS in Computer Science')"
    )
    institution: str = Field(
        description="School, university, or institution name"
    )
    year: str | None = Field(
        default=None,
        description="Graduation year or year range (e.g., '2020', '2018-2022')"
    )
    score: str | None = Field(
        default=None,
        description="Optional score or GPA (e.g., '3.8/4.0', '80%', 'First Class Honors')"
    )


class Employment(BaseModel):
    """Employment history entry."""
    
    company: str = Field(
        description="Company or organization name"
    )
    role: str = Field(
        description="Job title or role"
    )
    duration: str = Field(
        description="Employment duration (e.g., 'Jan 2020 - Dec 2022', '2 years 3 months')"
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities, achievements, or bullet points from this role"
    )


class StructuredResume(BaseModel):
    """
    Structured representation of a resume extracted via LLM parsing.
    This schema ensures consistent, validated resume data extraction.
    """
    
    skills: list[str] = Field(
        description="List of all technical and soft skills mentioned (e.g., 'Python', 'Leadership', 'AWS')"
    )
    experience_level: Literal["junior", "mid", "senior"] = Field(
        description="Candidate's experience level: 'junior' (0-2 years), 'mid' (2-5 years), 'senior' (5+ years)"
    )
    years_of_experience: float = Field(
        ge=0,
        description="Total years of professional work experience as a number"
    )
    # tech_stack: list[str] = Field(
    #     description="Technologies, programming languages, frameworks, and tools the candidate has used"
    # )
    projects: list[Project] = Field(
        default_factory=list,
        description="Notable projects mentioned in the resume"
    )
    education: list[Education] = Field(
        description="Educational background and qualifications"
    )
    employment_timeline: list[Employment] = Field(
        description="Work history in chronological order (most recent first preferred)"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Identified concerns, employment gaps, or red flags in the career timeline"
    )
    summary: str = Field(
        description="Professional summary: 2-3 sentences capturing the candidate's profile and key strengths"
    )
    
    # @field_validator("experience_level")
    # @classmethod
    # def validate_experience_level(cls, v: str) -> str:
    #     """Ensure experience level is valid."""
    #     valid_levels = {"junior", "mid", "senior"}
    #     if v not in valid_levels:
    #         return "mid"  # Default fallback
    #     return v
    
    # @field_validator("skills", "tech_stack", mode="after")
    # @classmethod
    # def deduplicate_lists(cls, v: list[str]) -> list[str]:
    #     """Remove duplicates while preserving order."""
    #     seen = set()
    #     result = []
    #     for item in v:
    #         item_lower = item.lower()
    #         if item_lower not in seen:
    #             seen.add(item_lower)
    #             result.append(item)
    #     return result


class ResumeParseRequest(BaseModel):
    text: str | None = None  # Raw text input (alternative to file upload)


class ResumeParseResponse(BaseModel):
    structured_resume: StructuredResume
    raw_text: str
    confidence: float = 0.0
    cached: bool = False
