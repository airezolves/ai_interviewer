"""Practical Test Generator — role-specific assessments."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import PracticalTest, PracticalTestVariant

SYSTEM_PROMPT = """You are a senior hiring manager creating practical technical assessments.
Generate a practical test with 3 difficulty variants (junior, mid, senior).
The test must be:
- Specific to the role type and candidate's domain
- Completable in 2-4 hours
- Evaluatable with clear criteria

Return JSON with:
- title: test title
- overview: 2-3 sentence overview
- variants: array of 3 objects, each with:
  - difficulty: "junior", "mid", or "senior"
  - task_description: detailed task description
  - dataset_scenario: what data/scenario they work with
  - expected_deliverables: list of expected outputs
  - time_limit: recommended time
  - evaluation_criteria: list of what to evaluate

Output ONLY valid JSON."""


async def generate_practical_test(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> PracticalTest:
    """Generate a practical assessment."""
    client = get_llm_client()

    role_context = {
        "data_scientist": "EDA + modeling task with a real-world dataset",
        "ml_engineer": "ML pipeline design and implementation challenge",
        "data_analyst": "Data analysis and visualization with business insights",
        "data_engineer": "ETL pipeline design and data modeling challenge",
        "analytics_engineer": "dbt modeling and analytics engineering task",
    }

    prompt = f"""Generate a practical assessment for:

ROLE: {role_type}
CONTEXT: {role_context.get(role_type, 'Technical assessment')}
CANDIDATE LEVEL: {structured_resume.get('experience_level', 'mid')}
CANDIDATE TECH STACK: {structured_resume.get('tech_stack', [])[:10]}
JD RESPONSIBILITIES: {structured_jd.get('responsibilities', [])[:5]}
JD REQUIRED SKILLS: {structured_jd.get('required_skills', [])[:10]}

Create a practical test that tests the core skills needed for this role.
Make it realistic — something they might actually encounter on the job."""

    try:
        data = await client.generate_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=5000)
        return PracticalTest(**data)
    except Exception:
        return PracticalTest(
            title=f"{role_type.replace('_', ' ').title()} Practical Assessment",
            overview="A practical assessment tailored to this role.",
            variants=[
                PracticalTestVariant(
                    difficulty="mid",
                    task_description="Complete the assessment based on the provided scenario.",
                    dataset_scenario="A sample dataset relevant to the role.",
                    expected_deliverables=["Analysis notebook", "Summary presentation"],
                    time_limit="3 hours",
                    evaluation_criteria=["Technical correctness", "Code quality", "Communication"],
                )
            ],
        )
