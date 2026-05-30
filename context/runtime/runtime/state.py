"""
Runtime State and Task Graph.

Tracks the execution state across loop iterations:
- Messages history
- Tool/agent/skill results
- Task graph (planned steps and their status)
- Observations and decisions
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("runtime.state")


class StepStatus(str, Enum):
    """Status of a task graph step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActionType(str, Enum):
    """Types of actions the planner can decide."""
    TOOL_CALL = "tool_call"
    AGENT_CALL = "agent_call"
    SKILL_CALL = "skill_call"
    FINAL_ANSWER = "final_answer"


@dataclass
class PlannerDecision:
    """A single decision from the planner LLM."""
    action: ActionType
    reasoning: str = ""
    # For tool_call
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    # For agent_call
    agent_name: Optional[str] = None
    agent_goal: Optional[str] = None
    agent_context: Optional[Dict[str, Any]] = None
    # For skill_call
    skill_name: Optional[str] = None
    skill_params: Optional[Dict[str, Any]] = None
    # For final_answer
    answer: Optional[str] = None
    # For batch tool_call (parallel execution)
    batch_tool_calls: Optional[List[Dict[str, Any]]] = None
    # For batch agent_call (parallel execution)
    batch_agent_calls: Optional[List[Dict[str, Any]]] = None
    # Classification metadata produced by the planner (mirrors the optional
    # fields on PlannerOutput). Kept as a free-form dict so we can extend it
    # without touching every call site. RuntimeState.update_metadata_from_decision
    # consumes this.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of executing a single step."""
    step_id: str
    action: ActionType
    name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class TaskGraphNode:
    """A node in the task graph."""
    step_id: str
    action: ActionType
    name: str
    goal: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[StepResult] = None
    depends_on: List[str] = field(default_factory=list)


class TaskGraph:
    """
    Tracks planned steps and their execution status.

    The planner can add steps dynamically as the loop progresses.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, TaskGraphNode] = {}

    def add_step(
        self,
        action: ActionType,
        name: str,
        goal: str,
        depends_on: Optional[List[str]] = None,
    ) -> str:
        """Add a step to the graph. Returns the step_id."""
        step_id = f"step_{len(self._nodes) + 1}_{name}"
        node = TaskGraphNode(
            step_id=step_id,
            action=action,
            name=name,
            goal=goal,
            depends_on=depends_on or [],
        )
        self._nodes[step_id] = node
        return step_id

    def mark_in_progress(self, step_id: str) -> None:
        if step_id in self._nodes:
            self._nodes[step_id].status = StepStatus.IN_PROGRESS

    def mark_completed(self, step_id: str, result: StepResult) -> None:
        if step_id in self._nodes:
            self._nodes[step_id].status = StepStatus.COMPLETED
            self._nodes[step_id].result = result

    def mark_failed(self, step_id: str, result: StepResult) -> None:
        if step_id in self._nodes:
            self._nodes[step_id].status = StepStatus.FAILED
            self._nodes[step_id].result = result

    @property
    def steps(self) -> List[TaskGraphNode]:
        return list(self._nodes.values())

    @property
    def completed_steps(self) -> List[TaskGraphNode]:
        return [n for n in self._nodes.values() if n.status == StepStatus.COMPLETED]

    @property
    def pending_steps(self) -> List[TaskGraphNode]:
        return [n for n in self._nodes.values() if n.status == StepStatus.PENDING]

    @property
    def all_done(self) -> bool:
        return all(
            n.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)
            for n in self._nodes.values()
        )

    def to_summary(self) -> Dict[str, Any]:
        """Serialize for LLM context — compact, no raw result data (memory_store handles that)."""
        return {
            "total_steps": len(self._nodes),
            "completed": len(self.completed_steps),
            "pending": len(self.pending_steps),
            "steps": [
                {
                    "step_id": n.step_id,
                    "action": n.action.value,
                    "name": n.name,
                    "goal": n.goal,
                    "status": n.status.value,
                }
                for n in self._nodes.values()
            ],
        }


class RuntimeState:
    """
    Mutable runtime state for a single execution.

    Accumulates tool results, agent results, observations,
    and tracks the overall execution lifecycle.
    """

    def __init__(
        self,
        user_query: str,
        session_history: Optional[List[Dict[str, Any]]] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        available_agents: Optional[List[Dict[str, Any]]] = None,
        available_skills: Optional[List[Dict[str, Any]]] = None,
        knowledge_context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 15,
    ) -> None:
        from a2a.orchestrator.config import (
            MAX_TOOL_RESULTS_ENTRIES,
            MAX_OBSERVATIONS_ENTRIES,
            MAX_STORED_RESULT_CHARS,
        )

        self.run_id: str = str(uuid.uuid4())
        self.user_query: str = user_query
        self.session_history: List[Dict[str, Any]] = session_history or []

        # Available resources
        self.available_tools: List[Dict[str, Any]] = available_tools or []
        self.available_agents: List[Dict[str, Any]] = available_agents or []
        self.available_skills: List[Dict[str, Any]] = available_skills or []
        self.knowledge_context: Dict[str, Any] = knowledge_context or {}

        # Execution tracking
        self.task_graph: TaskGraph = TaskGraph()
        self.observations: List[Dict[str, Any]] = []
        self.tool_results: Dict[str, Any] = {}
        self.agent_results: Dict[str, Any] = {}
        self.skill_results: Dict[str, Any] = {}

        # Memory guard limits
        self._max_tool_results = MAX_TOOL_RESULTS_ENTRIES
        self._max_observations = MAX_OBSERVATIONS_ENTRIES
        self._max_stored_result_chars = MAX_STORED_RESULT_CHARS

        # Loop state
        self.done: bool = False
        self.final_answer: Optional[str] = None
        self.iteration: int = 0
        self.max_iterations: int = max_iterations
        self.error: Optional[str] = None

        # DB-assigned runtime record ID (set by ExecutionEngine after create_runtime)
        self.runtime_id: Optional[str] = None

        # Events for streaming
        self.events: List[Dict[str, Any]] = []

        # ── Classification metadata ──
        # In the optimized flow these are produced by the Planner itself
        # (replacing the old intent_analysis node). They may also be seeded
        # by ExecutionEngine from any upstream hints for backward compat.
        self.intent: Optional[str] = None
        self.intent_domain: Optional[str] = None
        self.intent_entity: Optional[str] = None
        self.intent_action: Optional[str] = None
        self.complexity: Optional[str] = None
        self.intent_category: Optional[str] = None
        self.should_pass_history: Optional[bool] = None
        self.detected_language: Optional[str] = None
        self.matched_skill: Optional[str] = None
        self.needs_clarification: Optional[bool] = None
        self.clarification_reason: Optional[str] = None
        self.answer_mode: Optional[str] = None  # conversational|clarification|partial|data

        # Context manager integration (set by ExecutionEngine)
        self.context_manager: Any = None  # ContextManager instance
        self.agent_context: Any = None  # AgentContext instance

    # ── Planner metadata propagation ────────────────────────────────────

    def update_metadata_from_decision(self, decision: "PlannerDecision") -> None:
        """
        Merge classification metadata produced by the planner into the
        runtime state. Only overwrites fields the planner actually set
        (non-None) so earlier iterations stay authoritative when later
        ones omit a field.
        """
        meta = getattr(decision, "metadata", None) or {}
        for field_name in (
            "intent",
            "intent_domain",
            "intent_entity",
            "intent_action",
            "complexity",
            "intent_category",
            "should_pass_history",
            "detected_language",
            "matched_skill",
            "needs_clarification",
            "clarification_reason",
            "answer_mode",
        ):
            value = meta.get(field_name)
            if value is None:
                continue
            # Don't downgrade an already-set should_pass_history=True back to None.
            current = getattr(self, field_name, None)
            if current is None or current == "" or current == "unknown":
                setattr(self, field_name, value)
            elif field_name in ("answer_mode", "needs_clarification", "clarification_reason"):
                # The latest planner decision is most authoritative for these.
                setattr(self, field_name, value)

    def build_user_facing_fallback(self, reason: str) -> str:
        """
        Build a deterministic, user-facing fallback message for force-stop
        paths (max iterations, exhausted tools, exhausted agents, etc.).

        Imported lazily to avoid a circular import with planner_prompts.
        """
        from a2a.orchestrator.prompts.planner_prompts import (
            FALLBACK_MAX_ITERATIONS,
            FALLBACK_TOOLS_UNAVAILABLE,
            FALLBACK_AGENTS_UNAVAILABLE,
            FALLBACK_COLLECTED,
        )

        mapping = {
            "max_iterations": FALLBACK_MAX_ITERATIONS,
            "tools_unavailable": FALLBACK_TOOLS_UNAVAILABLE,
            "agents_unavailable": FALLBACK_AGENTS_UNAVAILABLE,
            "collected": FALLBACK_COLLECTED,
        }
        return mapping.get(reason, FALLBACK_COLLECTED)

    def add_observation(self, observation: Dict[str, Any]) -> None:
        """Record an observation from tool/agent/skill execution (bounded)."""
        self.observations.append(observation)
        if len(self.observations) > self._max_observations:
            self.observations = self.observations[-self._max_observations:]

    def store_tool_result(self, key: str, result: str) -> None:
        """Store a tool result with size capping and eviction."""
        # Truncate oversized results
        if len(result) > self._max_stored_result_chars:
            result = result[:self._max_stored_result_chars] + f"\n[TRUNCATED from {len(result):,} chars]"
        self.tool_results[key] = result
        # Evict oldest entries if over limit
        if len(self.tool_results) > self._max_tool_results:
            keys = list(self.tool_results.keys())
            for old_key in keys[:len(keys) - self._max_tool_results]:
                del self.tool_results[old_key]

    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a streaming event."""
        self.events.append({"type": event_type, "data": data})

    def get_context_for_planner(self) -> Dict[str, Any]:
        """Build context dict for the planner LLM."""
        return {
            "user_query": self.user_query,
            "iteration": self.iteration,
            "task_graph": self.task_graph.to_summary(),
            "observations": self.observations[-10:],  # Last 10 observations
            "tool_results": {
                k: (v if isinstance(v, str) else v)
                for k, v in self.tool_results.items()
            },
            "agent_results": {
                k: {
                    "success": v.get("success"),
                    "summary": v.get("summary"),
                }
                for k, v in self.agent_results.items()
            },
            "skill_results": self.skill_results,
            "available_tools_count": len(self.available_tools),
            "available_agents_count": len(self.available_agents),
        }

    def to_output(self) -> Dict[str, Any]:
        """Produce the final output dict for the internal orchestrator."""
        execution_plan = [
            {
                "step_id": s.step_id,
                "action": s.action.value,
                "name": s.name,
                "goal": s.goal,
                "status": s.status.value,
            }
            for s in self.task_graph.steps
        ]

        total = len(execution_plan)
        succeeded = sum(
            1 for s in self.task_graph.steps if s.status == StepStatus.COMPLETED
        )
        failed = sum(
            1 for s in self.task_graph.steps if s.status == StepStatus.FAILED
        )

        # Build agent_results from ALL successful tool/agent steps.
        # When context_render is available (from context manager), agent_results
        # contains only metadata (goals, tool names). The context_render is the
        # primary data source — ranked, deduplicated, and token-budgeted.
        # This prevents sending both raw data AND processed data to the synthesizer.
        agent_results: Dict[str, Any] = {}

        # If context manager is available, include its synthesizer-ready render
        context_render = ""
        if self.context_manager and self.agent_context:
            try:
                context_render = self.context_manager.render_for_final_llm(
                    self.agent_context
                )
            except Exception:
                context_render = ""

        has_context_render = bool(context_render)

        for node in self.task_graph.steps:
            if node.status != StepStatus.COMPLETED:
                continue
            if not node.result or not node.result.success:
                continue
            if node.action not in (ActionType.TOOL_CALL, ActionType.AGENT_CALL):
                continue

            if has_context_render:
                # Context manager already has the ranked, processed data.
                # Only pass metadata so the synthesizer knows what was collected.
                agent_results[node.step_id] = {
                    "success": True,
                    "goal": node.goal,
                    "tool_name": node.name,
                    "summary": f"Data collected for: {node.goal}",
                }
            else:
                # No context manager — fall back to raw truncation
                result_content = str(node.result.result) if node.result.result is not None else ""
                truncated = result_content[:8000]
                agent_results[node.step_id] = {
                    "success": True,
                    "agent": "AgentRuntime",
                    "goal": node.goal,
                    "tool_name": node.name,
                    "summary": truncated,
                    "results": [{"source": node.name, "content": truncated}],
                }

        output = {
            "execution_plan": execution_plan,
            "agent_results": agent_results,
            "execution_summary": (
                f"Executed {total} steps: {succeeded} succeeded, {failed} failed. "
                f"Iterations: {self.iteration}"
            ),
            "agent_events": self.events,
        }

        # Attach context manager render for the synthesizer to use
        if context_render:
            output["context_render"] = context_render

        # Pass runtime_id so synthesizer can complete the existing record
        if self.runtime_id:
            output["runtime_id"] = self.runtime_id

        # Final user-facing response (planner now writes this directly).
        output["final_response"] = self.final_answer or ""

        # Classification metadata produced by the planner — propagated up
        # so the orchestrator can populate analytics records and SSE events.
        for field_name in (
            "intent",
            "intent_domain",
            "intent_entity",
            "intent_action",
            "complexity",
            "intent_category",
            "should_pass_history",
            "detected_language",
            "matched_skill",
            "needs_clarification",
            "clarification_reason",
            "answer_mode",
        ):
            value = getattr(self, field_name, None)
            if value is not None:
                output[field_name] = value

        return output
