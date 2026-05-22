"""Flow Guide Generator — minute-by-minute interview structure."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import FlowSection

SYSTEM_PROMPT = """You are creating a minute-by-minute interview flow guide.
Structure a 60-minute interview into clear sections.
Each section must have:
- section: section name
- duration_minutes: how long this section takes
- activities: list of what to do in this section
- questions_mapped: list of question indices (0-based) to ask in this section

Typical structure:
1. Introduction & rapport (5 min)
2. Background & experience (10 min)
3. Technical deep-dive (20 min)
4. Practical/system design discussion (15 min)
5. Candidate questions & close (10 min)

Output ONLY a valid JSON array of section objects."""


async def generate_flow_guide(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> list[FlowSection]:
    """Generate interview flow guide."""
    client = get_llm_client()

    prompt = f"""Create an interview flow guide for a {role_type.replace('_', ' ')} interview.
Candidate level: {structured_resume.get('experience_level', 'mid')}
Seniority needed: {structured_jd.get('seniority', 'mid')}

Map 10 questions across the sections (indices 0-9).
Total duration: 60 minutes."""

    try:
        data = await client.generate_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=2000)
        if isinstance(data, list):
            return [FlowSection(**s) for s in data]
        return [FlowSection(**s) for s in data.get("sections", data)]
    except Exception:
        return [
            FlowSection(section="Introduction", duration_minutes=5, activities=["Welcome", "Set agenda", "Build rapport"], questions_mapped=[]),
            FlowSection(section="Background", duration_minutes=10, activities=["Walk through experience", "Clarify role transitions"], questions_mapped=[0, 1]),
            FlowSection(section="Technical Deep-Dive", duration_minutes=20, activities=["Core technical questions", "Follow-up probes"], questions_mapped=[2, 3, 4, 5]),
            FlowSection(section="Practical Discussion", duration_minutes=15, activities=["System design or case study", "Problem-solving approach"], questions_mapped=[6, 7, 8]),
            FlowSection(section="Wrap-up", duration_minutes=10, activities=["Candidate questions", "Next steps", "Thank and close"], questions_mapped=[9]),
        ]
