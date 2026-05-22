"""Match Scorer — compute resume-JD fit analysis."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import MatchAnalysis
from shared.schemas.resume import StructuredResume
from shared.schemas.kit import StructuredJD

SYSTEM_PROMPT = """You analyze the fit between a candidate's resume and a job description.
Return a JSON object with:
- overall_match_score: 0-100 percentage
- skill_matches: list of skills the candidate HAS that the JD requires
- skill_gaps: list of skills the JD requires that the candidate LACKS
- experience_fit: brief assessment of experience level fit
- level_calibration: is the candidate under/over/appropriately qualified?

Output ONLY valid JSON."""


async def compute_match_score(
    resume: StructuredResume,
    jd: StructuredJD,
    role_type: str,
) -> MatchAnalysis:
    """Compute match analysis between resume and JD."""
    client = get_llm_client()

    prompt = f"""Analyze the fit between this candidate and job:

CANDIDATE:
- Skills: {', '.join(resume.skills[:20])}
- Experience Level: {resume.experience_level}
- Years: {resume.years_of_experience}
- Tech Stack: {', '.join(resume.tech_stack[:15])}

JOB REQUIREMENTS:
- Required Skills: {', '.join(jd.required_skills[:15])}
- Nice to Have: {', '.join(jd.nice_to_have_skills[:10])}
- Seniority: {jd.seniority}
- Role Type: {role_type}"""

    try:
        data = await client.generate_json(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.3)
        return MatchAnalysis(**data)
    except Exception:
        # Basic match without LLM
        matched = set(s.lower() for s in resume.skills) & set(s.lower() for s in jd.required_skills)
        gaps = set(s.lower() for s in jd.required_skills) - set(s.lower() for s in resume.skills)
        score = (len(matched) / max(len(jd.required_skills), 1)) * 100
        return MatchAnalysis(
            overall_match_score=round(score, 1),
            skill_matches=list(matched)[:10],
            skill_gaps=list(gaps)[:10],
            experience_fit=f"{resume.experience_level} for {jd.seniority} role",
            level_calibration="unknown",
        )
