"""V2 ai_engine routes — drives the 3-agent kit flow.

These endpoints are called by the kit_orchestrator (or directly from the
gateway). They use the per-user LLM provider via `use_user_llm`.

Endpoints (mounted at root, but logically grouped under /v2):
  POST /v2/match                          — JD + resume → MatchScore (single shot)
  POST /v2/analyze-jd                     — raw JD → StructuredJD
  POST /v2/structure-resume               — raw resume text → StructuredResume
  POST /v2/interview/{kit_id}/start       — create session + first question
  POST /v2/interview/{kit_id}/answer      — submit answer → next question
  POST /v2/interview/{kit_id}/finalize    — run analysis agent → FinalReport
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select

from shared.database import get_database
from shared.database.models import (
    Kit,
    InterviewSession,
    QATurn,
    FinalAnalysis,
)
from shared.llm.user_provider import use_user_llm
from shared.schemas.kit import StructuredJD
from shared.schemas.resume import StructuredResume

from backend.ai_engine.app.agents.match_agent import run_match_agent
from backend.ai_engine.app.agents.runtime_agent import build_plan, decide_turn
from backend.ai_engine.app.agents.analysis_agent import run_analysis_agent
from backend.ai_engine.app.agents.jd_analyzer import analyze_jd
from backend.ai_engine.app.agents.resume_structurer import structure_resume
from backend.ai_engine.app.agents.schemas import MatchScore, InterviewPlan, TurnDecision

router = APIRouter(prefix="/v2")


# ─────────────────────────────────────────────────────────────────────
#  Request/response models
# ─────────────────────────────────────────────────────────────────────

class MatchRequest(BaseModel):
    structured_resume: dict
    structured_jd: dict
    role_type: str = "data_scientist"


class AnalyzeJDRequest(BaseModel):
    jd_text: str


class StructureResumeRequest(BaseModel):
    raw_text: str


class StartInterviewRequest(BaseModel):
    max_turns: int = 8


class AnswerRequest(BaseModel):
    answer: str


class TurnView(BaseModel):
    turn_index: int
    question: str
    question_type: Optional[str]
    topic: Optional[str]
    answer: Optional[str]


class InterviewStateView(BaseModel):
    session_id: str
    status: str
    current_turn_index: int
    max_turns: int
    plan: Optional[dict] = None
    turns: list[TurnView]
    next_question: Optional[str] = None
    finished: bool = False


# ─────────────────────────────────────────────────────────────────────
#  Match / JD / Resume endpoints
# ─────────────────────────────────────────────────────────────────────

@router.post("/match", response_model=MatchScore)
async def match(payload: MatchRequest, x_user_id: str = Header(...)):
    async with use_user_llm(x_user_id):
        return await run_match_agent(
            structured_resume=payload.structured_resume,
            structured_jd=payload.structured_jd,
            role_type=payload.role_type,
        )


@router.post("/analyze-jd", response_model=StructuredJD)
async def analyze_jd_endpoint(payload: AnalyzeJDRequest, x_user_id: str = Header(...)):
    async with use_user_llm(x_user_id):
        return await analyze_jd(payload.jd_text)


@router.post("/structure-resume", response_model=StructuredResume)
async def structure_resume_endpoint(payload: StructureResumeRequest, x_user_id: str = Header(...)):
    async with use_user_llm(x_user_id):
        return await structure_resume(payload.raw_text)


# ─────────────────────────────────────────────────────────────────────
#  Interview Q&A loop
# ─────────────────────────────────────────────────────────────────────

async def _load_kit(session, kit_id: uuid.UUID) -> Kit:
    res = await session.execute(select(Kit).where(Kit.id == kit_id))
    kit = res.scalar_one_or_none()
    if not kit:
        raise HTTPException(404, "Kit not found")
    return kit


async def _load_session(session, session_id: uuid.UUID) -> InterviewSession:
    res = await session.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Interview session not found")
    return s


def _turns_to_views(turns: list[QATurn]) -> list[TurnView]:
    return [
        TurnView(
            turn_index=t.turn_index,
            question=t.question,
            question_type=t.question_type,
            topic=t.topic,
            answer=t.answer,
        )
        for t in turns
    ]


def _transcript_dicts(turns: list[QATurn]) -> list[dict]:
    return [
        {
            "question": t.question,
            "answer": t.answer or "",
            "topic": t.topic or "",
            "question_type": t.question_type or "",
        }
        for t in turns
    ]


@router.post("/interview/{kit_id}/start", response_model=InterviewStateView)
async def start_interview(
    kit_id: str,
    payload: StartInterviewRequest,
    x_user_id: str = Header(...),
):
    """Create the interview session, generate the plan, and post the first question."""
    db = get_database()
    kid = uuid.UUID(kit_id)
    uid = uuid.UUID(x_user_id)

    async with db.async_session() as session:
        kit = await _load_kit(session, kid)
        if kit.user_id != uid:
            raise HTTPException(403, "Not your kit")
        if kit.proceed_decision != "proceed":
            raise HTTPException(409, "Kit has not been approved to proceed")
        if not kit.structured_jd or not kit.structured_resume:
            raise HTTPException(409, "Kit missing structured_jd / structured_resume")

        # Idempotency — return existing session if any.
        res = await session.execute(
            select(InterviewSession).where(InterviewSession.kit_id == kid)
        )
        existing = res.scalar_one_or_none()
        if existing:
            res2 = await session.execute(
                select(QATurn).where(QATurn.session_id == existing.id).order_by(QATurn.turn_index)
            )
            turns = list(res2.scalars().all())
            next_q = next((t.question for t in turns if t.answer is None), None)
            return InterviewStateView(
                session_id=str(existing.id),
                status=existing.status,
                current_turn_index=existing.current_turn_index,
                max_turns=existing.max_turns,
                plan=existing.plan,
                turns=_turns_to_views(turns),
                next_question=next_q,
                finished=existing.status != "in_progress",
            )

    # Build plan + first turn under the user's LLM config.
    async with use_user_llm(x_user_id):
        # We need to re-open a session because use_user_llm crosses an awaitable boundary
        async with db.async_session() as session:
            kit = await _load_kit(session, kid)
            match_summary = (kit.match_analysis or {}).get("summary", "")
            plan = await build_plan(
                structured_jd=kit.structured_jd or {},
                structured_resume=kit.structured_resume or {},
                match_summary=match_summary,
                max_turns=payload.max_turns,
            )
            first_q = plan.seed_questions[0] if plan.seed_questions else "Tell me about your background and what drew you to this role."
            first_topic = plan.topics[0] if plan.topics else "introduction"

            sess = InterviewSession(
                kit_id=kid,
                user_id=uid,
                status="in_progress",
                plan=plan.model_dump(),
                current_turn_index=0,
                max_turns=payload.max_turns,
            )
            session.add(sess)
            await session.flush()  # populate sess.id

            turn = QATurn(
                session_id=sess.id,
                turn_index=0,
                question=first_q,
                question_type="planned",
                topic=first_topic,
                agent_thoughts="Opening question from plan.",
            )
            session.add(turn)

            kit.status = "interviewing"
            await session.commit()

            return InterviewStateView(
                session_id=str(sess.id),
                status=sess.status,
                current_turn_index=sess.current_turn_index,
                max_turns=sess.max_turns,
                plan=sess.plan,
                turns=[TurnView(turn_index=0, question=first_q, question_type="planned", topic=first_topic, answer=None)],
                next_question=first_q,
                finished=False,
            )


@router.post("/interview/{kit_id}/answer", response_model=InterviewStateView)
async def answer_interview(
    kit_id: str,
    payload: AnswerRequest,
    x_user_id: str = Header(...),
):
    """Record the candidate's answer to the current question and let the
    runtime agent decide the next move."""
    db = get_database()
    kid = uuid.UUID(kit_id)
    uid = uuid.UUID(x_user_id)

    async with db.async_session() as session:
        kit = await _load_kit(session, kid)
        if kit.user_id != uid:
            raise HTTPException(403, "Not your kit")
        res = await session.execute(select(InterviewSession).where(InterviewSession.kit_id == kid))
        sess = res.scalar_one_or_none()
        if not sess:
            raise HTTPException(404, "Interview session not started")
        if sess.status != "in_progress":
            raise HTTPException(409, f"Interview is {sess.status}")

        res2 = await session.execute(
            select(QATurn).where(QATurn.session_id == sess.id).order_by(QATurn.turn_index)
        )
        turns: list[QATurn] = list(res2.scalars().all())
        # The "current" unanswered turn is the last one whose answer is None.
        current = next((t for t in reversed(turns) if t.answer is None), None)
        if not current:
            raise HTTPException(409, "No question awaiting an answer")

        current.answer = payload.answer
        current.answered_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(current)

        # Re-fetch so the transcript includes the just-answered turn.
        res3 = await session.execute(
            select(QATurn).where(QATurn.session_id == sess.id).order_by(QATurn.turn_index)
        )
        turns = list(res3.scalars().all())
        plan_dump = sess.plan or {}
        plan = InterviewPlan(**plan_dump) if plan_dump else None

    if plan is None:
        raise HTTPException(500, "Session has no plan")

    # Decide the next turn under the user's LLM config.
    transcript = _transcript_dicts(turns)
    # current_topic_index = number of *answered* topics that appear in plan.topics.
    answered_topics = [t.topic for t in turns if t.answer and t.topic]
    current_topic_index = min(len(set(answered_topics)), len(plan.topics))
    turns_used = sum(1 for t in turns if t.answer is not None)

    async with use_user_llm(x_user_id):
        decision: TurnDecision = await decide_turn(
            plan=plan,
            transcript=transcript,
            current_topic_index=current_topic_index,
            turns_used=turns_used,
            max_turns=sess.max_turns,
            last_answer=current.answer,
        )

    async with db.async_session() as session:
        # Re-load fresh for write
        sess = await _load_session(session, sess.id)
        kit = await _load_kit(session, kid)

        if decision.action == "wrap_up" or turns_used >= sess.max_turns:
            sess.status = "completed"
            sess.completed_at = datetime.now(timezone.utc)
            kit.status = "interviewing"  # transitions to 'analyzed' on /finalize
            await session.commit()

            res4 = await session.execute(
                select(QATurn).where(QATurn.session_id == sess.id).order_by(QATurn.turn_index)
            )
            turns = list(res4.scalars().all())
            return InterviewStateView(
                session_id=str(sess.id),
                status=sess.status,
                current_turn_index=sess.current_turn_index,
                max_turns=sess.max_turns,
                plan=sess.plan,
                turns=_turns_to_views(turns),
                next_question=None,
                finished=True,
            )

        next_index = sess.current_turn_index + 1
        next_topic = decision.topic or (plan.topics[current_topic_index] if current_topic_index < len(plan.topics) else "")
        new_turn = QATurn(
            session_id=sess.id,
            turn_index=next_index,
            question=decision.question,
            question_type=decision.question_type,
            topic=next_topic,
            agent_thoughts=decision.thought,
        )
        session.add(new_turn)
        sess.current_turn_index = next_index
        await session.commit()

        res5 = await session.execute(
            select(QATurn).where(QATurn.session_id == sess.id).order_by(QATurn.turn_index)
        )
        turns = list(res5.scalars().all())
        return InterviewStateView(
            session_id=str(sess.id),
            status=sess.status,
            current_turn_index=sess.current_turn_index,
            max_turns=sess.max_turns,
            plan=sess.plan,
            turns=_turns_to_views(turns),
            next_question=decision.question,
            finished=False,
        )


@router.get("/interview/{kit_id}", response_model=InterviewStateView)
async def get_interview_state(kit_id: str, x_user_id: str = Header(...)):
    db = get_database()
    kid = uuid.UUID(kit_id)
    async with db.async_session() as session:
        kit = await _load_kit(session, kid)
        if str(kit.user_id) != x_user_id:
            raise HTTPException(403, "Not your kit")
        res = await session.execute(select(InterviewSession).where(InterviewSession.kit_id == kid))
        sess = res.scalar_one_or_none()
        if not sess:
            raise HTTPException(404, "No interview session")
        res2 = await session.execute(
            select(QATurn).where(QATurn.session_id == sess.id).order_by(QATurn.turn_index)
        )
        turns = list(res2.scalars().all())
    next_q = next((t.question for t in turns if t.answer is None), None)
    return InterviewStateView(
        session_id=str(sess.id),
        status=sess.status,
        current_turn_index=sess.current_turn_index,
        max_turns=sess.max_turns,
        plan=sess.plan,
        turns=_turns_to_views(turns),
        next_question=next_q,
        finished=sess.status != "in_progress",
    )


@router.post("/interview/{kit_id}/finalize")
async def finalize_interview(kit_id: str, x_user_id: str = Header(...)):
    db = get_database()
    kid = uuid.UUID(kit_id)
    uid = uuid.UUID(x_user_id)

    async with db.async_session() as session:
        kit = await _load_kit(session, kid)
        if kit.user_id != uid:
            raise HTTPException(403, "Not your kit")
        res = await session.execute(select(InterviewSession).where(InterviewSession.kit_id == kid))
        sess = res.scalar_one_or_none()
        if not sess:
            raise HTTPException(404, "No interview session")

        res2 = await session.execute(
            select(QATurn).where(QATurn.session_id == sess.id).order_by(QATurn.turn_index)
        )
        turns = list(res2.scalars().all())
        transcript = _transcript_dicts(turns)
        match_dump = kit.match_analysis or {}
        sj = kit.structured_jd or {}
        sr = kit.structured_resume or {}
        role_type = kit.role_type
        sess_id = sess.id

        # Force session completed if not already.
        if sess.status == "in_progress":
            sess.status = "completed"
            sess.completed_at = datetime.now(timezone.utc)
            await session.commit()

    async with use_user_llm(x_user_id):
        report = await run_analysis_agent(
            structured_jd=sj,
            structured_resume=sr,
            match_analysis=match_dump,
            transcript=transcript,
            role_type=role_type,
        )

    async with db.async_session() as session:
        # Upsert FinalAnalysis
        res = await session.execute(select(FinalAnalysis).where(FinalAnalysis.kit_id == kid))
        existing = res.scalar_one_or_none()
        rec = report.model_dump()
        if existing:
            existing.session_id = sess_id
            existing.overall_score = rec["overall_score"]
            existing.dimension_scores = rec["dimension_scores"]
            existing.pros = rec["pros"]
            existing.cons = rec["cons"]
            existing.recommendation = rec["recommendation"]
            existing.role_suitability = rec["role_suitability"]
            existing.reasoning = rec["reasoning"]
        else:
            session.add(FinalAnalysis(
                kit_id=kid,
                session_id=sess_id,
                overall_score=rec["overall_score"],
                dimension_scores=rec["dimension_scores"],
                pros=rec["pros"],
                cons=rec["cons"],
                recommendation=rec["recommendation"],
                role_suitability=rec["role_suitability"],
                reasoning=rec["reasoning"],
            ))
        kit = await _load_kit(session, kid)
        kit.status = "complete"
        await session.commit()

    return report
