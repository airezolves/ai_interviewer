"""Generation routes — questions, tests, rubrics, red flags, flow guides."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_engine.app.generators.question_generator import generate_questions
from backend.ai_engine.app.generators.test_generator import generate_practical_test
from backend.ai_engine.app.generators.rubric_generator import generate_rubric
from backend.ai_engine.app.generators.red_flags_generator import analyze_red_flags
from backend.ai_engine.app.generators.flow_generator import generate_flow_guide
from shared.schemas.kit import (
    Question, PracticalTest, Rubric, RedFlag, FlowSection, MatchAnalysis,
)

router = APIRouter()


class GenerationContext(BaseModel):
    """Context passed to all generators."""
    structured_resume: dict
    structured_jd: dict
    match_analysis: dict
    role_type: str = "data_scientist"


@router.post("/generate-questions", response_model=list[Question])
async def generate_questions_endpoint(ctx: GenerationContext):
    """Generate tailored interview questions with model answers."""
    return await generate_questions(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)


@router.post("/generate-test", response_model=PracticalTest)
async def generate_test_endpoint(ctx: GenerationContext):
    """Generate a practical assessment with 3 difficulty variants."""
    return await generate_practical_test(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)


@router.post("/generate-rubric", response_model=Rubric)
async def generate_rubric_endpoint(ctx: GenerationContext):
    """Generate a weighted scoring rubric."""
    return await generate_rubric(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)


@router.post("/generate-red-flags", response_model=list[RedFlag])
async def generate_red_flags_endpoint(ctx: GenerationContext):
    """Identify red flags and generate probe questions."""
    return await analyze_red_flags(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)


@router.post("/generate-flow", response_model=list[FlowSection])
async def generate_flow_endpoint(ctx: GenerationContext):
    """Generate an interview flow guide."""
    return await generate_flow_guide(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)
