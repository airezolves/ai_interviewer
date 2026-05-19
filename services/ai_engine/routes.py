"""AI Engine service routes."""

from fastapi import APIRouter

from shared.schemas.common import APIResponse, HealthResponse
from services.ai_engine.schemas import (
    AnalyzeJDRequest,
    GenerateQuestionsRequest,
    GenerateAssessmentRequest,
    GenerateRubricRequest,
    GenerateRedFlagsRequest,
    GenerateFlowGuideRequest,
    GenerateFullKitRequest,
    FullKitResponse,
)
from services.ai_engine.service import AIEngineService

router = APIRouter(prefix="/ai", tags=["ai_engine"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(service="ai_engine")


@router.post("/analyze-jd", response_model=APIResponse)
async def analyze_jd(request: AnalyzeJDRequest):
    """Analyze a job description into structured data."""
    service = AIEngineService()
    result = await service.analyze_jd(request.jd_text)
    return APIResponse(data=result)


@router.post("/generate-questions", response_model=APIResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """Generate interview questions with model answers."""
    service = AIEngineService()
    result = await service.generate_questions(
        request.jd_analysis, request.resume_data, request.role_type
    )
    return APIResponse(data=result)


@router.post("/generate-assessment", response_model=APIResponse)
async def generate_assessment(request: GenerateAssessmentRequest):
    """Generate practical assessment."""
    service = AIEngineService()
    result = await service.generate_assessment(
        request.jd_analysis, request.resume_data, request.role_type
    )
    return APIResponse(data=result)


@router.post("/generate-rubric", response_model=APIResponse)
async def generate_rubric(request: GenerateRubricRequest):
    """Generate scoring rubric."""
    service = AIEngineService()
    result = await service.generate_rubric(
        request.jd_analysis, request.resume_data, request.role_type
    )
    return APIResponse(data=result)


@router.post("/generate-red-flags", response_model=APIResponse)
async def generate_red_flags(request: GenerateRedFlagsRequest):
    """Identify candidate red flags."""
    service = AIEngineService()
    result = await service.generate_red_flags(
        request.jd_analysis, request.resume_data, request.role_type
    )
    return APIResponse(data=result)


@router.post("/generate-flow-guide", response_model=APIResponse)
async def generate_flow_guide(request: GenerateFlowGuideRequest):
    """Generate interview flow guide."""
    service = AIEngineService()
    result = await service.generate_flow_guide(
        request.jd_analysis, request.resume_data, request.role_type
    )
    return APIResponse(data=result)


@router.post("/generate-kit-full", response_model=APIResponse[FullKitResponse])
async def generate_full_kit(request: GenerateFullKitRequest):
    """Generate a complete interview kit (all sections in parallel)."""
    service = AIEngineService()
    result = await service.generate_full_kit(
        request.jd_text, request.resume_data, request.role_type
    )
    return APIResponse(data=result)
