"""Practical assessment generation prompts."""

from services.ai_engine.prompts.base import build_context_block

ASSESSMENT_PROMPT = """You are an expert at designing practical technical assessments for {role_type} roles. Create a personalized practical test for this candidate.

{context}

=== INSTRUCTIONS ===
Generate a practical assessment with THREE difficulty variants (Junior/Mid/Senior). The assessment should:
- Be completable in 2-4 hours
- Test the skills most relevant to the JD
- Be calibrated to the candidate's experience level
- Include realistic data/scenarios

For EACH variant, provide:
1. "level": "junior" | "mid" | "senior"
2. "title": Short assessment title
3. "description": Detailed task description (2-3 paragraphs)
4. "dataset_description": What data/scenario they'll work with
5. "deliverables": List of expected outputs
6. "time_limit": Suggested time (e.g., "2 hours")
7. "evaluation_criteria": List of criteria with weights
8. "bonus_challenges": 1-2 optional stretch goals
9. "tools_allowed": Suggested tools/languages

The assessment MUST:
- Be specific enough to prevent generic answers
- Have clear success criteria
- Test practical skills, not trivia
- Be relevant to the actual job responsibilities

Return as JSON: {{"assessments": [...], "recommended_level": "junior|mid|senior"}}
"""


def get_assessment_prompt(jd_analysis: dict, resume_data: dict, role_type: str) -> str:
    context = build_context_block(jd_analysis, resume_data)
    return ASSESSMENT_PROMPT.format(
        role_type=role_type.replace("_", " ").title(),
        context=context,
    )
