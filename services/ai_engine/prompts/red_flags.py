"""Red flags identification prompts."""

from services.ai_engine.prompts.base import build_context_block

RED_FLAGS_PROMPT = """You are a senior hiring manager reviewing a candidate's resume for a {role_type} position. Identify potential concerns and prepare diplomatic probe questions.

{context}

=== INSTRUCTIONS ===
Analyze the candidate's resume against the JD and identify 3-5 potential concerns. For EACH:
1. "flag": Brief description of the concern (1 sentence)
2. "severity": "low" | "medium" | "high"
3. "category": "skill_gap" | "experience_gap" | "career_pattern" | "inconsistency" | "cultural_fit"
4. "evidence": What in the resume triggers this concern
5. "probe_questions": 2 diplomatic questions to explore this in the interview
6. "mitigating_factors": What might explain this away (1 sentence)

Concerns to look for:
- Skill gaps between resume and JD requirements
- Short tenures or frequent job changes
- Employment gaps
- Unclear contributions (team achievements without personal role)
- Over-qualification or under-qualification
- Technology mismatches
- Missing expected progression

Be DIPLOMATIC — these are probing questions, not accusations.

Return as JSON: {{"red_flags": [...], "overall_risk_level": "low|medium|high", "summary": "..."}}
"""


def get_red_flags_prompt(jd_analysis: dict, resume_data: dict, role_type: str) -> str:
    context = build_context_block(jd_analysis, resume_data)
    return RED_FLAGS_PROMPT.format(
        role_type=role_type.replace("_", " ").title(),
        context=context,
    )
