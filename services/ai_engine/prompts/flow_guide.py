"""Interview flow guide generation prompts."""

from services.ai_engine.prompts.base import build_context_block

FLOW_GUIDE_PROMPT = """You are an interview coach helping structure a 60-minute technical interview for a {role_type} position.

{context}

=== INSTRUCTIONS ===
Create a minute-by-minute interview structure. The interview should flow naturally and cover all critical areas.

Provide:
1. "total_duration": Total minutes (default 60)
2. "sections": List of sections, each with:
   - "name": Section name (e.g., "Introduction & Rapport Building")
   - "duration_minutes": How many minutes
   - "start_minute": When this section starts
   - "purpose": What this section achieves
   - "questions_to_ask": List of 1-3 specific questions from the generated question set
   - "tips": 1-2 interviewer tips for this section
   - "transition": How to smoothly move to the next section

Standard structure:
- Introduction & Rapport (5 min)
- Background Deep-Dive (10 min)
- Technical Questions (20 min)
- Practical/Problem-Solving Discussion (15 min)
- Candidate Questions & Wrap-Up (10 min)

Also provide:
- "pre_interview_checklist": 5 things to prepare before the interview
- "dos_and_donts": 3 dos and 3 don'ts for this specific interview
- "closing_notes": How to end positively regardless of outcome

Return as JSON: {{"total_duration": 60, "sections": [...], "pre_interview_checklist": [...], "dos_and_donts": {{"dos": [...], "donts": [...]}}, "closing_notes": "..."}}
"""


def get_flow_guide_prompt(jd_analysis: dict, resume_data: dict, role_type: str) -> str:
    context = build_context_block(jd_analysis, resume_data)
    return FLOW_GUIDE_PROMPT.format(
        role_type=role_type.replace("_", " ").title(),
        context=context,
    )
