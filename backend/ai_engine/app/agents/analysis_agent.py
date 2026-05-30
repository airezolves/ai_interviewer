"""Analysis Agent — final scoring after the interview completes.

Takes JD, resume, match analysis and full Q&A transcript, returns a
structured FinalReport with per-dimension scores and a hire recommendation.
"""

from __future__ import annotations

import logging

from shared.llm import get_instructor_client
from backend.ai_engine.app.agents.schemas import FinalReport

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a hiring committee chair writing the final
evaluation memo. Use ALL of: the job description, the resume, the upfront
match analysis, and the live interview transcript.

Required dimension keys (0-100 each): technical, communication,
problem_solving, role_fit, culture_alignment.

Compute overall_score as a weighted blend (technical 30%, role_fit 25%,
problem_solving 20%, communication 15%, culture_alignment 10%).

Recommendation rules:
  ≥75 → hire | 55-74 → maybe | <55 → no_hire

Pros/cons MUST cite specific transcript evidence (paraphrased). Keep each bullet 1-2 sentences.
`reasoning` should be 2-4 short paragraphs weaving resume → interview signal → recommendation.

Output STRICT FinalReport."""


async def run_analysis_agent(
    structured_jd: dict,
    structured_resume: dict,
    match_analysis: dict,
    transcript: list[dict],
    role_type: str,
) -> FinalReport:
    client, model, extra = get_instructor_client(json_mode=True)

    transcript_str = "\n\n".join(
        f"Q{i+1} [{t.get('topic','')}, {t.get('question_type','')}]: {t['question']}\n"
        f"A{i+1}: {t.get('answer','(no answer)')}"
        for i, t in enumerate(transcript)
    ) or "(no interview turns recorded)"

    user = (
        f"=== ROLE TYPE ===\n{role_type}\n\n"
        f"=== JOB DESCRIPTION ===\n"
        f"Required skills: {', '.join(structured_jd.get('required_skills', [])[:20])}\n"
        f"Seniority: {structured_jd.get('seniority','')}\n"
        f"Responsibilities: {'; '.join(structured_jd.get('responsibilities', [])[:6])}\n\n"
        f"=== CANDIDATE ===\n"
        f"Skills: {', '.join(structured_resume.get('skills', [])[:25])}\n"
        f"Years: {structured_resume.get('years_of_experience','')}\n"
        f"Summary: {structured_resume.get('summary','')}\n\n"
        f"=== UPFRONT MATCH ANALYSIS ===\n"
        f"overall_score: {match_analysis.get('overall_score','?')}\n"
        f"recommendation: {match_analysis.get('recommendation','?')}\n"
        f"summary: {match_analysis.get('summary','')}\n\n"
        f"=== LIVE INTERVIEW TRANSCRIPT ===\n{transcript_str}\n\n"
        "Produce the FinalReport now."
    )

    report: FinalReport = client.chat.completions.create(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        response_model=FinalReport,
        max_retries=2,
        temperature=0.3,
        **extra,
    )
    logger.info("Analysis agent: overall=%.1f recommendation=%s", report.overall_score, report.recommendation)
    return report
