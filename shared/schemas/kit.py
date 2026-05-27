"""Kit-related schemas — the core data models."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from enum import Enum


class RoleType(str, Enum):
    DATA_SCIENTIST = "data_scientist"
    ML_ENGINEER = "ml_engineer"
    DATA_ANALYST = "data_analyst"
    DATA_ENGINEER = "data_engineer"
    ANALYTICS_ENGINEER = "analytics_engineer"


class KitStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


# ─── Sub-components ────────────────────────────────────────────

class StructuredJD(BaseModel):
    """
    Structured representation of a job description extracted via LLM parsing.
    This schema ensures consistent, validated JD data extraction for interview kit generation.
    """
    
    required_skills: list[str] = Field(
        description="Mandatory skills, technologies, or qualifications explicitly required for the role (e.g., 'Python', '5+ years experience', 'SQL', 'Machine Learning')"
    )
    nice_to_have_skills: list[str] = Field(
        default_factory=list,
        description="Preferred, optional, or bonus skills that would be beneficial but not mandatory (e.g., 'AWS certification', 'Spark', 'Team leadership experience')"
    )
    seniority: Literal["junior", "mid", "senior"] = Field(
        description="Required seniority level based on years of experience, responsibilities, and job description tone: 'junior' (0-2 years), 'mid' (2-5 years), 'senior' (5+ years or leadership)"
    )
    responsibilities: list[str] = Field(
        description="Key job responsibilities, day-to-day tasks, and expected deliverables for this role"
    )
    team_context: str = Field(
        default="",
        description="Information about the team structure, size, reporting relationships, and collaboration dynamics (e.g., 'Reports to Head of Data, works with 5-person analytics team')"
    )
    company_info: str = Field(
        default="",
        description="Brief company description including industry, size, stage, mission, or culture if mentioned in the JD"
    )
    
    # @field_validator("seniority")
    # @classmethod
    # def validate_seniority(cls, v: str) -> str:
    #     """Ensure seniority is valid."""
    #     valid_levels = {"junior", "mid", "senior"}
    #     if v not in valid_levels:
    #         return "mid"  # Default fallback
    #     return v
    
    # @field_validator("required_skills", "nice_to_have_skills", mode="after")
    # @classmethod
    # def deduplicate_skills(cls, v: list[str]) -> list[str]:
    #     """Remove duplicates while preserving order."""
    #     seen = set()
    #     result = []
    #     for item in v:
    #         item_lower = item.lower().strip()
    #         if item_lower and item_lower not in seen:
    #             seen.add(item_lower)
    #             result.append(item.strip())
    #     return result
    
    # @field_validator("responsibilities", mode="after")
    # @classmethod
    # def clean_responsibilities(cls, v: list[str]) -> list[str]:
    #     """Remove empty and duplicate responsibilities."""
    #     seen = set()
    #     result = []
    #     for item in v:
    #         item_clean = item.strip()
    #         if item_clean and item_clean not in seen:
    #             seen.add(item_clean)
    #             result.append(item_clean)
    #     return result


class Question(BaseModel):
    question: str
    category: str  # behavioral, technical, system_design
    what_it_tests: str
    model_answer: str
    follow_up_probes: list[str] = []
    difficulty: str = "medium"  # easy, medium, hard


class PracticalTestVariant(BaseModel):
    difficulty: str  # junior, mid, senior
    task_description: str
    dataset_scenario: str
    expected_deliverables: list[str] = []
    time_limit: str = "2 hours"
    evaluation_criteria: list[str] = []


class PracticalTest(BaseModel):
    title: str
    overview: str
    variants: list[PracticalTestVariant] = []


class RubricCriterion(BaseModel):
    name: str
    weight_pct: int
    description: str
    score_1: str  # What 1 looks like
    score_3: str  # What 3 looks like
    score_5: str  # What 5 looks like


class Rubric(BaseModel):
    criteria: list[RubricCriterion] = []
    pass_threshold: float = 3.0
    total_weight: int = 100


class RedFlag(BaseModel):
    concern: str
    severity: str  # low, medium, high
    probe_question: str
    what_to_listen_for: str


class FlowSection(BaseModel):
    section: str
    duration_minutes: int
    activities: list[str] = []
    questions_mapped: list[int] = []  # indices into questions list


class MatchAnalysis(BaseModel):
    overall_match_score: float  # 0-100
    skill_matches: list[str] = []
    skill_gaps: list[str] = []
    experience_fit: str = ""
    level_calibration: str = ""


# ─── Kit (full output) ─────────────────────────────────────────

class KitGenerateRequest(BaseModel):
    jd_text: str
    resume_text: str | None = None
    role_type: RoleType = RoleType.DATA_SCIENTIST


class KitResponse(BaseModel):
    id: UUID
    title: str | None = None
    role_type: str
    status: str
    match_analysis: MatchAnalysis | None = None
    questions: list[Question] | None = None
    practical_test: PracticalTest | None = None
    rubric: Rubric | None = None
    red_flags: list[RedFlag] | None = None
    flow_guide: list[FlowSection] | None = None
    pdf_url: str | None = None
    share_token: UUID | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class KitListResponse(BaseModel):
    kits: list[KitResponse]
    total: int
    page: int
    per_page: int


# ─── Generation Job ────────────────────────────────────────────

class JobStatus(BaseModel):
    job_id: UUID
    kit_id: UUID
    status: str
    current_step: str | None = None
    progress_pct: int = 0
    error_message: str | None = None
