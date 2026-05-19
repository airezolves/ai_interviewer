"""AI Engine service schemas."""

from pydantic import BaseModel


class JDAnalysis(BaseModel):
    """Structured job description analysis."""
    role_title: str = ""
    seniority_level: str = ""  # junior, mid, senior, lead, principal
    required_skills: list[str] = []
    nice_to_haves: list[str] = []
    responsibilities: list[str] = []
    team_context: str = ""
    industry: str = ""
    company_size: str = ""


class GenerateQuestionsRequest(BaseModel):
    jd_analysis: dict
    resume_data: dict
    role_type: str = "data_scientist"


class GenerateAssessmentRequest(BaseModel):
    jd_analysis: dict
    resume_data: dict
    role_type: str = "data_scientist"


class GenerateRubricRequest(BaseModel):
    jd_analysis: dict
    resume_data: dict
    role_type: str = "data_scientist"


class GenerateRedFlagsRequest(BaseModel):
    jd_analysis: dict
    resume_data: dict
    role_type: str = "data_scientist"


class GenerateFlowGuideRequest(BaseModel):
    jd_analysis: dict
    resume_data: dict
    role_type: str = "data_scientist"


class GenerateFullKitRequest(BaseModel):
    """Request to generate a complete interview kit."""
    jd_text: str
    resume_data: dict
    role_type: str = "data_scientist"


class AnalyzeJDRequest(BaseModel):
    jd_text: str
    role_type: str = "data_scientist"


class FullKitResponse(BaseModel):
    """Complete interview kit response."""
    jd_analysis: dict
    questions: dict
    assessment: dict
    rubric: dict
    red_flags: dict
    flow_guide: dict
