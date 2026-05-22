"""Kit-related schemas — the core data models."""

from pydantic import BaseModel
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
    required_skills: list[str] = []
    nice_to_have_skills: list[str] = []
    seniority: str = "mid"
    responsibilities: list[str] = []
    team_context: str = ""
    company_info: str = ""


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
