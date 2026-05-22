"""Rubric Generator — weighted scoring criteria."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import Rubric, RubricCriterion

SYSTEM_PROMPT = """You are creating an objective interview scoring rubric.
Generate 8 evaluation criteria with weights that sum to 100.
Each criterion needs:
- name: criterion name
- weight_pct: percentage weight (all must sum to 100)
- description: what this evaluates
- score_1: what a score of 1 (poor) looks like
- score_3: what a score of 3 (adequate) looks like
- score_5: what a score of 5 (excellent) looks like

Return JSON with:
- criteria: array of criterion objects
- pass_threshold: minimum average score to pass (typically 3.0-3.5)
- total_weight: 100

Output ONLY valid JSON."""


async def generate_rubric(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> Rubric:
    """Generate a scoring rubric."""
    client = get_llm_client()

    prompt = f"""Create a scoring rubric for evaluating a {role_type.replace('_', ' ')} candidate.

JD REQUIRED SKILLS: {structured_jd.get('required_skills', [])[:10]}
JD RESPONSIBILITIES: {structured_jd.get('responsibilities', [])[:5]}
SENIORITY: {structured_jd.get('seniority', 'mid')}

Create 8 criteria that comprehensively evaluate this candidate.
Include both technical skills AND soft skills (communication, problem-solving).
Weights should reflect the JD priorities."""

    try:
        data = await client.generate_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=4000)
        return Rubric(**data)
    except Exception:
        return Rubric(
            criteria=[
                RubricCriterion(name="Technical Skills", weight_pct=25, description="Core technical competency",
                                score_1="Cannot explain basics", score_3="Solid understanding", score_5="Expert-level depth"),
                RubricCriterion(name="Problem Solving", weight_pct=20, description="Analytical approach",
                                score_1="No structured approach", score_3="Clear methodology", score_5="Creative, optimal solutions"),
                RubricCriterion(name="Communication", weight_pct=15, description="Clarity of explanation",
                                score_1="Unclear, rambling", score_3="Clear and concise", score_5="Exceptional storytelling"),
                RubricCriterion(name="Experience Depth", weight_pct=15, description="Hands-on experience",
                                score_1="Theoretical only", score_3="Practical experience", score_5="Deep production experience"),
                RubricCriterion(name="Culture Fit", weight_pct=10, description="Team alignment",
                                score_1="Misaligned values", score_3="Good fit", score_5="Exceptional alignment"),
                RubricCriterion(name="Learning Ability", weight_pct=15, description="Growth mindset",
                                score_1="Rigid, defensive", score_3="Open to feedback", score_5="Actively seeks growth"),
            ],
            pass_threshold=3.0,
            total_weight=100,
        )
