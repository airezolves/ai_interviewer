"""Kit-related schemas — the core data models."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from enum import Enum


class RoleType(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"
    DATA_SCIENTIST = "data_scientist"
    ML_ENGINEER = "ml_engineer"
    DATA_ANALYST = "data_analyst"
    DATA_ENGINEER = "data_engineer"
    ANALYTICS_ENGINEER = "analytics_engineer"
    DEVOPS = "devops"
    MOBILE = "mobile"
    ENGINEERING_MANAGER = "engineering_manager"


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
    """Interview question with model answer and evaluation criteria."""
    
    model_config = {"protected_namespaces": ()}  # Allow 'model_' prefix in field names
    
    question: str = Field(
        description="The actual interview question to ask the candidate. Should be clear, specific, and relevant to their background and the role requirements."
    )
    category: str = Field(
        description="Question category: 'technical_depth' (verify technical skills), 'behavioral' (past behavior and approach), 'system_design' (architecture and scalability), 'domain_knowledge' (industry-specific knowledge), 'problem_solving' (analytical thinking), or 'gap_verification' (probe identified skill gaps)"
    )
    what_it_tests: str = Field(
        description="Clear explanation of what specific skill, competency, or trait this question evaluates in the candidate"
    )
    model_answer: str = Field(
        description="A strong example answer that demonstrates the expected depth and quality. Should be 2-4 sentences showing what good looks like."
    )
    follow_up_probes: list[str] = Field(
        default_factory=list,
        description="2-4 follow-up questions to dig deeper based on their initial response. These should probe for specifics, edge cases, or deeper understanding."
    )
    difficulty: str = Field(
        default="medium",
        description="Question difficulty level: 'easy' (basic understanding), 'medium' (practical application), 'hard' (deep expertise or complex scenarios)"
    )
    relevance_rationale: str = Field(
        default="",
        description="Brief explanation of why this question is particularly relevant for THIS candidate based on their resume or the JD requirements"
    )


class QuestionSet(BaseModel):
    """Complete set of interview questions generated for a candidate."""
    
    questions: list[Question] = Field(
        description="Comprehensive list of 15-20 interview questions covering all aspects of evaluation: technical depth, behavioral patterns, system design, domain knowledge, problem-solving, and gap verification"
    )


class TechnicalQuestion(BaseModel):
    """A single practical technical question/task."""
    
    question: str = Field(
        description="The practical question or task to be completed. Should be specific, hands-on, and testable."
    )
    difficulty: str = Field(
        description="Question difficulty: 'junior' (0-2 years), 'mid' (2-5 years), 'senior' (5+ years)"
    )
    what_it_tests: str = Field(
        description="Specific aspect of the skill being tested (e.g., 'basic syntax', 'optimization', 'architectural design')"
    )
    expected_approach: str = Field(
        description="Brief description of how a competent candidate should approach this question (2-3 sentences)"
    )
    evaluation_criteria: list[str] = Field(
        description="3-5 specific criteria to evaluate the answer (e.g., 'code correctness', 'edge case handling', 'time complexity')"
    )
    time_estimate: str = Field(
        default="15-20 minutes",
        description="Estimated time for a qualified candidate to complete this question"
    )


class SkillAssessment(BaseModel):
    """Practical assessment for a specific technical skill."""
    
    skill_name: str = Field(
        description="The technical skill being assessed (e.g., 'Python', 'SQL', 'System Design', 'Machine Learning')"
    )
    why_this_skill: str = Field(
        description="Brief rationale for why this skill is being tested based on the JD requirements and candidate's claimed expertise"
    )
    questions: list[TechnicalQuestion] = Field(
        description="5 questions total: 2 junior level, 2 mid level, 1 senior level"
    )


class PracticalTestSet(BaseModel):
    """Complete set of skill-based practical assessments."""
    
    assessments: list[SkillAssessment] = Field(
        description="Up to 8 skill-based assessments, each containing 5 questions (2 junior, 2 mid, 1 senior). Total: 40 questions max."
    )
    overall_time_estimate: str = Field(
        default="2-3 hours",
        description="Total estimated time to complete the full assessment"
    )
    recommended_approach: str = Field(
        default="",
        description="Instructions for the candidate on how to approach the test (e.g., 'Start with skills you're most confident in', 'Code quality matters more than completion')"
    )


# Legacy models for backward compatibility
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
    """
    Analysis of how well a candidate's resume matches a job description.
    Provides scoring and detailed breakdown of skill alignment and experience fit.
    """
    
    overall_match_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall fit score from 0-100 representing how well the candidate matches the job requirements. Higher scores indicate better alignment."
    )
    skill_matches: list[str] = Field(
        default_factory=list,
        description="Skills and technologies the candidate POSSESSES that the job description requires or prefers (intersection of candidate skills and JD requirements)"
    )
    skill_gaps: list[str] = Field(
        default_factory=list,
        description="Required or important skills from the JD that the candidate's resume does NOT demonstrate (skills the candidate needs to develop or clarify)"
    )
    experience_fit: str = Field(
        description="Narrative assessment of how the candidate's experience level, years, and background align with job requirements. Include specific observations about relevant experience."
    )
    level_calibration: Literal["underqualified", "appropriate", "overqualified", "unknown"] = Field(
        description="Whether the candidate is 'underqualified' (below required level), 'appropriate' (good fit), 'overqualified' (exceeds requirements), or 'unknown' (insufficient information)"
    )
    
    # @field_validator("overall_match_score")
    # @classmethod
    # def validate_score_range(cls, v: float) -> float:
    #     """Ensure match score is within valid range."""
    #     return max(0.0, min(100.0, v))
    
    # @field_validator("skill_matches", "skill_gaps", mode="after")
    # @classmethod
    # def deduplicate_and_clean_skills(cls, v: list[str]) -> list[str]:
    #     """Remove duplicates and empty values from skill lists."""
    #     seen = set()
    #     result = []
    #     for item in v:
    #         item_clean = item.strip()
    #         item_lower = item_clean.lower()
    #         if item_clean and item_lower not in seen:
    #             seen.add(item_lower)
    #             result.append(item_clean)
    #     return result
    
    # @field_validator("level_calibration")
    # @classmethod
    # def validate_calibration(cls, v: str) -> str:
    #     """Ensure level calibration is valid."""
    #     valid_calibrations = {"underqualified", "appropriate", "overqualified", "unknown"}
    #     if v not in valid_calibrations:
    #         return "unknown"  # Default fallback
    #     return v


# ─── Kit (full output) ─────────────────────────────────────────

class KitGenerateRequest(BaseModel):
    """Request schema for kit generation - used internally after file processing."""
    jd_text: str
    resume_text: str | None = None
    role_type: RoleType
    structured_resume: dict | None = None  # Pre-structured resume from Gateway (avoids duplicate LLM call)


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
