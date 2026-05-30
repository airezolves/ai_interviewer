"""Pydantic schemas used by the three agents (Match, Runtime, Analysis)."""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────
#  Match Agent
# ─────────────────────────────────────────────────────────────────────

class DimensionMatch(BaseModel):
    score: float = Field(..., ge=0, le=100, description="0-100 sub-score for this dimension")
    reasoning: str = Field(..., description="Why this score, with concrete evidence")


class MatchScore(BaseModel):
    """Single-shot LLM output for the Match Agent.

    Contains all sub-dimensions plus an overall_score derived weighted average.
    """
    technical_match: DimensionMatch
    experience_match: DimensionMatch
    skills_match: DimensionMatch
    education_match: DimensionMatch

    overall_score: float = Field(..., ge=0, le=100, description="Holistic 0-100 fit score")
    recommendation: Literal["strong_proceed", "proceed", "borderline", "deny"] = Field(
        ..., description="High-level guidance for the recruiter."
    )

    matched_skills: list[str] = Field(default_factory=list, description="Skills the candidate clearly possesses that the JD requires")
    missing_skills: list[str] = Field(default_factory=list, description="Required skills not evidenced in the resume")
    strengths: list[str] = Field(default_factory=list, description="Top 3-5 standout strengths for this role")
    gaps: list[str] = Field(default_factory=list, description="Top 3-5 concerning gaps or risks")
    summary: str = Field(..., description="2-4 sentence executive summary of fit")


# ─────────────────────────────────────────────────────────────────────
#  Runtime Agent (per-turn decision)
# ─────────────────────────────────────────────────────────────────────

class InterviewPlan(BaseModel):
    """Initial plan the Runtime Agent produces from JD/resume/match."""
    topics: list[str] = Field(..., description="Ordered list of high-level topics to probe")
    seed_questions: list[str] = Field(..., description="One opening question per topic, in order")
    rationale: str = Field(..., description="Why this plan covers the most decision-relevant ground")


class TurnDecision(BaseModel):
    """The 'think → act → observe' decision the agent makes after each answer."""
    thought: str = Field(..., description="Internal reasoning about the prior answer and what to ask next")
    action: Literal["ask_followup", "ask_next_planned", "wrap_up"] = Field(...)
    question: str = Field(..., description="The exact question to put to the candidate (ignored when action == 'wrap_up')")
    question_type: Literal["planned", "followup", "clarification", "wrap_up"] = Field(...)
    topic: str = Field(default="", description="Topic this turn is about")


# ─────────────────────────────────────────────────────────────────────
#  Analysis Agent (final report)
# ─────────────────────────────────────────────────────────────────────

class FinalReport(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    dimension_scores: dict[str, float] = Field(
        ...,
        description="Per-dimension 0-100 scores. Required keys: technical, communication, problem_solving, role_fit, culture_alignment.",
    )
    pros: list[str] = Field(..., description="Concrete strengths observed across resume + interview")
    cons: list[str] = Field(..., description="Concrete weaknesses or risks observed")
    role_suitability: str = Field(..., description="Detailed assessment of fit for the specific role")
    recommendation: Literal["hire", "no_hire", "maybe"] = Field(...)
    reasoning: str = Field(..., description="Multi-paragraph rationale weaving evidence from resume, JD and interview transcript")
