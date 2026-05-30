"""Match Agent — single LLM call producing a structured MatchScore.

Uses the per-user model factory (Instructor + Pydantic) so the candidate's
recruiter sees scores generated from their own configured model.
"""

from __future__ import annotations

import logging

from shared.llm import get_instructor_client
from backend.ai_engine.app.agents.schemas import MatchScore

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an expert technical recruiter and hiring manager.

Your task: in a SINGLE pass, produce a complete fit analysis between a job
description and a candidate's resume.

Score four dimensions on 0-100:
  • technical_match   — depth/breadth of required technical skills
  • experience_match  — years and relevance of prior roles
  • skills_match      — coverage of explicit JD required + nice-to-have skills
  • education_match   — alignment of qualifications with role expectations

Then derive an `overall_score` as a weighted blend (technical 35%, experience 30%,
skills 25%, education 10%). Round to one decimal.

Map overall_score → recommendation:
  ≥85: strong_proceed | 70-84: proceed | 55-69: borderline | <55: deny

Be specific. Cite resume evidence in `reasoning`. Output MUST conform to the
MatchScore schema. Do not invent skills the resume does not show."""


def _format_resume(resume: dict) -> str:
    skills = ", ".join((resume.get("skills") or [])[:30])
    emp = resume.get("employment_timeline") or []
    emp_str = "\n".join(
        f"- {e.get('role','')} @ {e.get('company','')} ({e.get('duration','')})"
        for e in emp[:5]
    )
    edu = resume.get("education") or []
    edu_str = "\n".join(f"- {e.get('degree','')} @ {e.get('institution','')}" for e in edu[:3])
    return (
        f"Experience level: {resume.get('experience_level','unknown')}\n"
        f"Years of experience: {resume.get('years_of_experience','?')}\n"
        f"Summary: {resume.get('summary','')}\n\n"
        f"Skills: {skills}\n\n"
        f"Employment:\n{emp_str or '- (none)'}\n\n"
        f"Education:\n{edu_str or '- (none)'}\n"
    )


def _format_jd(jd: dict) -> str:
    req = ", ".join((jd.get("required_skills") or [])[:25])
    nth = ", ".join((jd.get("nice_to_have_skills") or [])[:15])
    resp = "\n".join(f"- {r}" for r in (jd.get("responsibilities") or [])[:6])
    return (
        f"Seniority: {jd.get('seniority','unknown')}\n"
        f"Required skills: {req}\n"
        f"Nice-to-have: {nth}\n\n"
        f"Responsibilities:\n{resp or '- (none)'}\n\n"
        f"Team context: {jd.get('team_context','')}\n"
        f"Company info: {jd.get('company_info','')}\n"
    )


async def run_match_agent(
    structured_resume: dict,
    structured_jd: dict,
    role_type: str,
) -> MatchScore:
    """Execute the Match Agent — a single Instructor call producing MatchScore."""
    client, model, extra = get_instructor_client(json_mode=True)

    user_prompt = (
        f"=== ROLE TYPE ===\n{role_type}\n\n"
        f"=== JOB DESCRIPTION ===\n{_format_jd(structured_jd)}\n"
        f"=== CANDIDATE RESUME ===\n{_format_resume(structured_resume)}\n"
        "Produce the complete MatchScore now."
    )

    result: MatchScore = client.chat.completions.create(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_model=MatchScore,
        max_retries=2,
        temperature=0.2,
        **extra,
    )
    logger.info("Match agent: overall_score=%.1f (%s)", result.overall_score, result.recommendation)
    return result
