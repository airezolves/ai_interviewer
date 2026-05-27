"""Analysis routes — JD analysis, match scoring."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_engine.app.generators.jd_analyzer import analyze_jd
from backend.ai_engine.app.generators.match_scorer import compute_match_score
from shared.schemas.kit import StructuredJD, MatchAnalysis
from shared.schemas.resume import StructuredResume

router = APIRouter()


class AnalyzeJDRequest(BaseModel):
    jd_text: str


class MatchScoreRequest(BaseModel):
    structured_resume: dict
    structured_jd: dict
    role_type: str = "data_scientist"


@router.post("/analyze-jd", response_model=StructuredJD)
async def analyze_jd_endpoint(data: AnalyzeJDRequest):
    """Analyze a job description into structured format."""
    return await analyze_jd(data.jd_text)


@router.post("/match-score", response_model=MatchAnalysis)
async def match_score_endpoint(data: MatchScoreRequest):
    """Compute resume-JD match score."""
    # Handle nested structured_resume if coming from ResumeParseResponse
    resume_data = data.structured_resume
    if "structured_resume" in resume_data:
        # It's a ResumeParseResponse, extract the nested structured_resume
        resume_data = resume_data["structured_resume"]
    
    resume = StructuredResume(**resume_data)
    jd = StructuredJD(**data.structured_jd)
    return await compute_match_score(resume, jd, data.role_type)
