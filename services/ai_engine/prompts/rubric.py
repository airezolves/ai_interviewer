"""Scoring rubric generation prompts."""

from services.ai_engine.prompts.base import build_context_block

RUBRIC_PROMPT = """You are an expert at creating objective interview scoring rubrics for {role_type} roles. Generate a comprehensive rubric for evaluating this candidate.

{context}

=== INSTRUCTIONS ===
Generate a scoring rubric with 8 criteria. For EACH criterion:
1. "name": Criterion name (e.g., "Technical Depth", "Communication")
2. "weight": Percentage weight (all must sum to 100)
3. "description": What this criterion evaluates (1 sentence)
4. "scale": Rating explanations:
   - "1": What a 1/5 (poor) looks like
   - "3": What a 3/5 (adequate) looks like
   - "5": What a 5/5 (exceptional) looks like
5. "must_have_signals": Key behaviors/answers that indicate competence
6. "disqualifying_signals": Answers that suggest a hard no

Also provide:
- "pass_threshold": Minimum weighted score to recommend hire (e.g., 3.5/5)
- "strong_hire_threshold": Score that indicates a strong hire (e.g., 4.2/5)
- "overall_recommendation_guide": How to interpret the final score

The rubric MUST:
- Be specific to this role and JD
- Include both technical and soft-skill criteria
- Have clear, observable scoring anchors (not vague)
- Weight technical skills appropriately for the seniority level

Return as JSON: {{"criteria": [...], "pass_threshold": X, "strong_hire_threshold": X, "overall_recommendation_guide": "..."}}
"""


def get_rubric_prompt(jd_analysis: dict, resume_data: dict, role_type: str) -> str:
    context = build_context_block(jd_analysis, resume_data)
    return RUBRIC_PROMPT.format(
        role_type=role_type.replace("_", " ").title(),
        context=context,
    )
