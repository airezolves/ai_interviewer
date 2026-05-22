"""Red Flags Generator — identify concerns and probe questions."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import RedFlag

SYSTEM_PROMPT = """You are a senior hiring manager analyzing a candidate's resume for potential concerns.
Identify 3-5 potential red flags or areas to probe. Be diplomatic, not accusatory.
Each flag must have:
- concern: what the concern is
- severity: "low", "medium", or "high"
- probe_question: a diplomatic question to investigate this
- what_to_listen_for: what response would alleviate or confirm the concern

Output ONLY a valid JSON array of flag objects."""


async def analyze_red_flags(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> list[RedFlag]:
    """Identify red flags and generate probe questions."""
    client = get_llm_client()

    prompt = f"""Analyze this candidate for potential concerns:

CANDIDATE:
- Experience: {structured_resume.get('experience_level', 'mid')} ({structured_resume.get('years_of_experience', 0)} years)
- Skills: {structured_resume.get('skills', [])[:15]}
- Employment: {structured_resume.get('employment_timeline', [])[:5]}
- Gaps identified: {structured_resume.get('gaps', [])}

JD REQUIREMENTS:
- Required: {structured_jd.get('required_skills', [])[:10]}
- Seniority: {structured_jd.get('seniority', 'mid')}

MATCH ANALYSIS:
- Score: {match_analysis.get('overall_match_score', 0)}%
- Skill Gaps: {match_analysis.get('skill_gaps', [])}

Identify 3-5 areas of concern. Consider:
- Employment gaps
- Skill mismatches vs JD
- Short tenures
- Unclear contributions (team vs individual)
- Over/under qualification"""

    try:
        data = await client.generate_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=3000)
        if isinstance(data, list):
            return [RedFlag(**f) for f in data]
        return [RedFlag(**f) for f in data.get("red_flags", data)]
    except Exception:
        return [
            RedFlag(
                concern="Skill gap in key requirement",
                severity="medium",
                probe_question="I noticed X isn't prominently featured in your background. Can you tell me about your experience with it?",
                what_to_listen_for="Look for indirect experience or willingness to learn quickly.",
            )
        ]
