"""LangGraph definition for the 3-agent kit flow.

Macro flow:
    START → match → [proceed_gate?]
                       ↓ deny → END
                       ↓ proceed → interview → analysis → END

In production each of these nodes is invoked from a different HTTP request
(match runs at kit creation; interview turns are driven by /interview/answer;
analysis is triggered by /interview/finalize). The graph here is the source
of truth for valid transitions and is what drives the kit's `status` field.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, START, END


class KitFlowState(TypedDict, total=False):
    kit_id: str
    user_id: str
    role_type: str
    structured_jd: Dict[str, Any]
    structured_resume: Dict[str, Any]
    match_score: Dict[str, Any]
    proceed_decision: Optional[Literal["proceed", "denied"]]
    interview_session_id: Optional[str]
    transcript: list[dict]
    final_report: Optional[Dict[str, Any]]


# ─── Nodes ──────────────────────────────────────────────────────────

async def match_node(state: KitFlowState) -> KitFlowState:
    """Runs the Match Agent."""
    from backend.ai_engine.app.agents.match_agent import run_match_agent

    score = await run_match_agent(
        structured_resume=state["structured_resume"],
        structured_jd=state["structured_jd"],
        role_type=state.get("role_type", ""),
    )
    return {"match_score": score.model_dump()}


async def interview_node(state: KitFlowState) -> KitFlowState:
    """Marker node — the interactive turns themselves run outside the graph
    (via /interview/answer), so this node simply asserts that an interview
    session is established."""
    return {"interview_session_id": state.get("interview_session_id")}


async def analysis_node(state: KitFlowState) -> KitFlowState:
    """Runs the Analysis Agent on the completed transcript."""
    from backend.ai_engine.app.agents.analysis_agent import run_analysis_agent

    report = await run_analysis_agent(
        structured_jd=state["structured_jd"],
        structured_resume=state["structured_resume"],
        match_analysis=state.get("match_score") or {},
        transcript=state.get("transcript") or [],
        role_type=state.get("role_type", ""),
    )
    return {"final_report": report.model_dump()}


# ─── Routing ────────────────────────────────────────────────────────

def proceed_router(state: KitFlowState) -> Literal["interview", "__end__"]:
    """Conditional after match — recruiter must set proceed_decision."""
    return "interview" if state.get("proceed_decision") == "proceed" else "__end__"


# ─── Compile ────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(KitFlowState)
    g.add_node("match", match_node)
    g.add_node("interview", interview_node)
    g.add_node("analysis", analysis_node)
    g.add_edge(START, "match")
    g.add_conditional_edges("match", proceed_router, {"interview": "interview", "__end__": END})
    g.add_edge("interview", "analysis")
    g.add_edge("analysis", END)
    return g.compile()


GRAPH = build_graph()
