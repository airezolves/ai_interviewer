"""Question generation prompts."""

from services.ai_engine.prompts.base import build_context_block

QUESTIONS_PROMPT = """You are an expert technical interviewer specializing in {role_type} roles. Generate a comprehensive set of interview questions tailored to this specific candidate and job.

{context}

=== INSTRUCTIONS ===
Generate 10 interview questions divided into:
- 3 behavioral questions (test soft skills, leadership, collaboration)
- 5 technical questions (test domain expertise matching JD requirements)
- 2 situational/problem-solving questions (test how they think)

For EACH question, provide:
1. "question": The actual question text
2. "category": "behavioral" | "technical" | "situational"
3. "tests": What skill/competency this question evaluates
4. "difficulty": "easy" | "medium" | "hard"
5. "model_answer": A detailed ideal answer (3-5 sentences)
6. "follow_ups": 2 follow-up probes to dig deeper
7. "red_flags": What bad answers look like (1-2 sentences)
8. "green_flags": What great answers include (1-2 sentences)

Questions MUST be:
- Specific to the candidate's background (reference their projects/experience)
- Aligned with the JD requirements
- Progressively more difficult
- NOT generic/googleable

Return as JSON: {{"questions": [...]}}
"""


def get_questions_prompt(jd_analysis: dict, resume_data: dict, role_type: str) -> str:
    context = build_context_block(jd_analysis, resume_data)
    return QUESTIONS_PROMPT.format(
        role_type=role_type.replace("_", " ").title(),
        context=context,
    )
