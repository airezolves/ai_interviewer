"""Generation routes — questions, tests, rubrics, red flags, flow guides."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_engine.app.generators.question_generator import generate_questions
from backend.ai_engine.app.generators.test_generator import generate_practical_test
from backend.ai_engine.app.generators.rubric_generator import generate_rubric
from backend.ai_engine.app.generators.red_flags_generator import analyze_red_flags
from backend.ai_engine.app.generators.flow_generator import generate_flow_guide

router = APIRouter()


class GenerationContext(BaseModel):
    """Context passed to all generators."""
    structured_resume: dict
    structured_jd: dict
    match_analysis: dict
    role_type: str = "data_scientist"
    questions: list[dict] | None = None  # Optional: Only for flow generator


@router.post("/generate-questions")
async def generate_questions_endpoint(ctx: GenerationContext):
    """Generate tailored interview questions with model answers.
    
    Returns: JSON array of Question objects
    """
    questions = await generate_questions(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)
    # Convert Pydantic models to dicts for JSON serialization
    return [q.model_dump() for q in questions]


@router.post("/generate-test")
async def generate_test_endpoint(ctx: GenerationContext):
    """Generate a practical assessment with 3 difficulty variants.
    
    Returns: JSON object with skill-based test structure converted to legacy format
    """
    test = await generate_practical_test(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)
    # Convert Pydantic model to dict for JSON serialization
    return test.model_dump()


@router.post("/generate-rubric")
async def generate_rubric_endpoint(ctx: GenerationContext):
    """Generate a weighted scoring rubric.
    
    Returns: JSON object with scoring criteria
    """
    rubric = await generate_rubric(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)
    return rubric.model_dump() if hasattr(rubric, 'model_dump') else rubric


@router.post("/generate-red-flags")
async def generate_red_flags_endpoint(ctx: GenerationContext):
    """Identify red flags and generate probe questions.
    
    Returns: JSON array of RedFlag objects
    """
    flags = await analyze_red_flags(ctx.structured_resume, ctx.structured_jd, ctx.match_analysis, ctx.role_type)
    return [f.model_dump() for f in flags] if flags and hasattr(flags[0], 'model_dump') else flags


@router.post("/generate-flow")
async def generate_flow_endpoint(ctx: GenerationContext):
    """Generate an interview flow guide.
    
    Returns: JSON array of FlowSection objects
    
    NOTE: If questions are provided in context, they will be used for intelligent
    question mapping. Otherwise, generic indices will be used.
    """
    flow = await generate_flow_guide(
        ctx.structured_resume, 
        ctx.structured_jd, 
        ctx.match_analysis, 
        ctx.role_type,
        ctx.questions  # Pass questions if available
    )
    return [s.model_dump() for s in flow] if flow and hasattr(flow[0], 'model_dump') else flow
