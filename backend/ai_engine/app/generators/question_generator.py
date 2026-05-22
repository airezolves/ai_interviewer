"""Question Generator — tailored interview questions with model answers."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import Question

SYSTEM_PROMPT = """You are a senior technical interviewer generating personalized interview questions.
Generate 10 interview questions based on the candidate-JD match context.
Mix of categories: behavioral (3), technical (5), system_design (2).
Each question must have:
- question: the actual question text
- category: "behavioral", "technical", or "system_design"
- what_it_tests: what skill/trait this evaluates
- model_answer: a strong answer (2-3 sentences)
- follow_up_probes: 2-3 follow-up questions
- difficulty: "easy", "medium", or "hard"

Personalize questions to the candidate's actual experience and the role requirements.
Output ONLY a valid JSON array of question objects."""


async def generate_questions(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> list[Question]:
    """Generate tailored interview questions."""
    client = get_llm_client()

    prompt = f"""Generate interview questions for this context:

ROLE TYPE: {role_type}
CANDIDATE SKILLS: {structured_resume.get('skills', [])[:15]}
CANDIDATE EXPERIENCE: {structured_resume.get('experience_level', 'mid')} ({structured_resume.get('years_of_experience', 0)} years)
CANDIDATE TECH STACK: {structured_resume.get('tech_stack', [])[:10]}

JD REQUIRED SKILLS: {structured_jd.get('required_skills', [])[:10]}
JD SENIORITY: {structured_jd.get('seniority', 'mid')}
JD RESPONSIBILITIES: {structured_jd.get('responsibilities', [])[:5]}

MATCH SCORE: {match_analysis.get('overall_match_score', 0)}%
SKILL GAPS: {match_analysis.get('skill_gaps', [])[:5]}
SKILL MATCHES: {match_analysis.get('skill_matches', [])[:5]}

Generate 10 personalized interview questions. Focus on:
1. Verifying claimed skills (technical)
2. Probing gaps identified in match analysis
3. Behavioral questions about relevant projects
4. System design appropriate to seniority level"""

    try:
        data = await client.generate_json(prompt=prompt, system=SYSTEM_PROMPT, max_tokens=6000)
        if isinstance(data, list):
            return [Question(**q) for q in data]
        return [Question(**q) for q in data.get("questions", data)]
    except Exception:
        return _fallback_questions(role_type)


def _fallback_questions(role_type: str) -> list[Question]:
    """Basic fallback questions if LLM fails."""
    return [
        Question(
            question="Walk me through a recent project where you applied machine learning to solve a business problem.",
            category="behavioral",
            what_it_tests="Communication, problem-solving, ML application",
            model_answer="A strong answer describes the problem, approach, implementation, and measurable impact.",
            follow_up_probes=["What was the biggest challenge?", "How did you measure success?"],
            difficulty="medium",
        ),
        Question(
            question="Explain the bias-variance tradeoff and how you handle it in practice.",
            category="technical",
            what_it_tests="ML fundamentals, practical experience",
            model_answer="Bias is underfitting, variance is overfitting. Use cross-validation, regularization, ensemble methods.",
            follow_up_probes=["Give a specific example", "How do you detect overfitting?"],
            difficulty="medium",
        ),
    ]
