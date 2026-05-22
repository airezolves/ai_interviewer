"""JD Analyzer — parse job descriptions into structured data."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import StructuredJD

SYSTEM_PROMPT = """You are a job description analyzer for technical hiring.
Given a raw job description, extract and return a JSON object with:
- required_skills: list of mandatory skills mentioned
- nice_to_have_skills: list of preferred/bonus skills
- seniority: "junior", "mid", or "senior" based on years/tone
- responsibilities: list of key responsibilities
- team_context: brief description of team/department
- company_info: brief company description if available

Output ONLY valid JSON."""


async def analyze_jd(jd_text: str) -> StructuredJD:
    """Analyze a job description into structured format."""
    client = get_llm_client()

    try:
        data = await client.generate_json(
            prompt=f"Analyze this job description:\n\n{jd_text[:5000]}",
            system=SYSTEM_PROMPT,
            temperature=0.3,
        )
        return StructuredJD(**data)
    except Exception:
        # Fallback: return basic structure
        return StructuredJD(
            required_skills=[],
            nice_to_have_skills=[],
            seniority="mid",
            responsibilities=[],
            team_context="",
            company_info="",
        )
