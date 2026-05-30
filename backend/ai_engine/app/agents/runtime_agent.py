"""Runtime Agent — interactive 'think → act → observe' interview loop.

The agent maintains a plan (created once at session start) and, after every
candidate answer, decides whether to ask a follow-up, advance to the next
planned topic, or wrap up.
"""

from __future__ import annotations

import logging
from typing import Optional

from shared.llm import get_instructor_client
from backend.ai_engine.app.agents.schemas import InterviewPlan, TurnDecision

logger = logging.getLogger(__name__)


PLAN_SYSTEM = """You are a senior interviewer. From the JD, resume, and match
analysis, design a focused interview plan covering the most decision-relevant
ground in the available turns. Prefer probing risk areas (skill gaps,
experience mismatches) and validating claimed strengths.

Pick 5-8 topics, each with a strong opening question. Output STRICT InterviewPlan."""


TURN_SYSTEM = """You are conducting a live interview using a 'think → act → observe' loop.

After every candidate answer, decide:
  • ask_followup      — the answer needs deeper probing (vague, partial, or claims worth verifying)
  • ask_next_planned  — the topic is sufficiently covered; advance to the next planned question
  • wrap_up          — enough signal collected OR max turns reached; close the interview gracefully

Rules:
  • Always cite the prior answer in your `thought`.
  • Each follow-up must add information, not repeat.
  • Prefer ask_next_planned once a topic is reasonably covered.
  • Be concise — questions should be 1-2 sentences.

Output STRICT TurnDecision."""


async def build_plan(
    structured_jd: dict,
    structured_resume: dict,
    match_summary: str,
    max_turns: int,
) -> InterviewPlan:
    client, model, extra = get_instructor_client(json_mode=True)
    user = (
        f"Max turns: {max_turns}\n\n"
        f"Match summary: {match_summary}\n\n"
        f"JD required skills: {', '.join(structured_jd.get('required_skills', [])[:20])}\n"
        f"JD seniority: {structured_jd.get('seniority','')}\n\n"
        f"Resume skills: {', '.join(structured_resume.get('skills', [])[:25])}\n"
        f"Resume summary: {structured_resume.get('summary','')}\n"
        "Build the InterviewPlan now."
    )
    plan: InterviewPlan = client.chat.completions.create(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": user},
        ],
        response_model=InterviewPlan,
        max_retries=2,
        temperature=0.4,
        **extra,
    )
    return plan


async def decide_turn(
    plan: InterviewPlan,
    transcript: list[dict],
    current_topic_index: int,
    turns_used: int,
    max_turns: int,
    last_answer: Optional[str],
) -> TurnDecision:
    """One step of the think-act-observe loop.

    `transcript` is a list of {question, answer, topic, question_type} dicts (most
    recent last). `last_answer` is the answer to the very last question (or None
    if this is the opening turn).
    """
    client, model, extra = get_instructor_client(json_mode=True)

    if turns_used >= max_turns - 1:
        # Force wrap_up to keep within budget.
        return TurnDecision(
            thought="Max turns reached; wrapping up.",
            action="wrap_up",
            question="Thank you — that's all the questions I had. Is there anything you'd like to add?",
            question_type="wrap_up",
            topic="",
        )

    transcript_str = "\n\n".join(
        f"Q{i+1} [{t.get('topic','')}]: {t['question']}\nA{i+1}: {t.get('answer','(no answer)')}"
        for i, t in enumerate(transcript[-8:])  # last 8 turns of context
    )

    next_topic = plan.topics[current_topic_index] if current_topic_index < len(plan.topics) else "wrap-up"
    next_seed = plan.seed_questions[current_topic_index] if current_topic_index < len(plan.seed_questions) else ""

    user = (
        f"Turns used: {turns_used} / {max_turns}\n"
        f"Current topic index: {current_topic_index} of {len(plan.topics)}\n"
        f"Next planned topic: {next_topic}\n"
        f"Next planned seed question: {next_seed}\n\n"
        f"=== TRANSCRIPT SO FAR ===\n{transcript_str or '(empty — this is the first turn)'}\n\n"
        f"=== LAST ANSWER ===\n{last_answer or '(none yet)'}\n\n"
        "Make the TurnDecision now."
    )

    decision: TurnDecision = client.chat.completions.create(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": TURN_SYSTEM},
            {"role": "user", "content": user},
        ],
        response_model=TurnDecision,
        max_retries=2,
        temperature=0.5,
        **extra,
    )
    if decision.action != "ask_followup" and not decision.topic:
        # Hint the topic for downstream storage if the model omitted it.
        decision = decision.model_copy(update={"topic": next_topic if decision.action != "wrap_up" else ""})
    return decision
