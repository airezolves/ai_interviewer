"""
Planner — LLM-based reasoning engine.

The planner is the reasoning brain of the runtime. It:
- Understands the user's task
- Decides the next action (tool_call / agent_call / skill_call / final_answer)
- Does NOT execute anything — only produces decisions

The planner receives full context (state, memory, tool schemas, agent schemas,
skill schemas) and returns a PlannerDecision.
"""

from __future__ import annotations

from a2a.shared.utils import load_env_from_path

load_env_from_path()

import os
import logging
from typing import Any, Dict, List, Optional

from a2a.orchestrator.runtime.state import (
    ActionType,
    PlannerDecision,
    RuntimeState,
)
from a2a.shared.model_factory import get_instructor_client

logger = logging.getLogger("runtime.planner")


# Pydantic models for structured LLM output
from pydantic import BaseModel, Field


class ToolCallAction(BaseModel):
    """A single tool call in a batch."""
    tool_name: str = Field(description="Name of the MCP tool to call")
    tool_args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the tool",
    )


class AgentCallAction(BaseModel):
    """A single agent call in a batch."""
    agent_name: str = Field(description="Name of the A2A agent to call")
    agent_goal: str = Field(description="Goal/task for the agent")


class PlannerOutput(BaseModel):
    """Structured output from the planner LLM."""
    reasoning: str = Field(
        description=(
            "ONE short operational sentence describing what to do next or why "
            "this is the final answer. Internal-only: never shown to the user. "
            "Do NOT include chain-of-thought."
        )
    )
    action: str = Field(
        description=(
            "The action type. Must be exactly one of: "
            "'tool_call', 'agent_call', 'skill_call', 'final_answer'. "
            "Always use singular form (tool_call, not tool_calls) even for batch operations."
        )
    )
    # Single tool call fields
    tool_name: Optional[str] = Field(None, description="Tool name for a single tool call")
    tool_args: Optional[Dict[str, Any]] = Field(
        None, description="Tool arguments for a single tool call"
    )
    # Batch tool calls (parallel execution)
    tool_calls: Optional[List[ToolCallAction]] = Field(
        None,
        description=(
            "Multiple tool calls to execute in parallel. "
            "Use when processing a list of items (e.g., fetching RCA for multiple incidents)."
        ),
    )
    # Single agent call fields
    agent_name: Optional[str] = Field(None, description="Agent name for a single agent call")
    agent_goal: Optional[str] = Field(None, description="Agent goal for a single agent call")
    # Batch agent calls (parallel execution)
    agent_calls: Optional[List[AgentCallAction]] = Field(
        None,
        description=(
            "Multiple agent calls to execute in parallel. "
            "Use when delegating to multiple agents concurrently."
        ),
    )
    # Skill call fields
    skill_name: Optional[str] = Field(None, description="Skill name (if action=skill_call)")
    # Final answer — when action='final_answer' this IS the user-facing reply.
    answer: Optional[str] = Field(
        None,
        description=(
            "When action='final_answer', this is the EXACT text shown to the "
            "user. Apply the FINAL ANSWER RULES from the system prompt: no "
            "tool/internal names, no fabricated data, match the user's "
            "language, use markdown for data answers."
        ),
    )

    # ── Classification metadata (replaces former intent_analysis node) ──
    intent: Optional[str] = Field(
        None, description="Short semantic label, e.g. 'greeting', 'blast_radius'."
    )
    intent_domain: Optional[str] = Field(
        None,
        description="One of: infra, iam, code, vault, cloud, network, devices, general.",
    )
    intent_entity: Optional[str] = Field(
        None, description="Primary entity type referenced (or null)."
    )
    intent_action: Optional[str] = Field(
        None, description="Action/verb implied (or null)."
    )
    complexity: Optional[str] = Field(
        None, description="'simple' or 'complex' (default 'complex' if unsure)."
    )
    intent_category: Optional[str] = Field(
        None,
        description=(
            "For complex queries only: one of risk_and_impact, "
            "incident_and_history, resource_and_topology, operational_guidance, "
            "generic. Null for simple."
        ),
    )
    should_pass_history: Optional[bool] = Field(
        None, description="True if the query depends on conversation history."
    )
    detected_language: Optional[str] = Field(
        None, description="Detected language NAME (e.g. 'English', 'Hindi')."
    )
    matched_skill: Optional[str] = Field(
        None,
        description=(
            "Best-matching skill name from AVAILABLE SKILLS, or null. "
            "Setting this does NOT auto-apply a skill — you still need a "
            "skill_call action."
        ),
    )
    needs_clarification: Optional[bool] = Field(
        None, description="True if the query is ambiguous and needs clarification."
    )
    clarification_reason: Optional[str] = Field(
        None, description="Short note describing what is missing."
    )
    answer_mode: Optional[str] = Field(
        None,
        description=(
            "Set when action=final_answer. One of: conversational, "
            "clarification, partial, data."
        ),
    )


def _build_planner_system_prompt(
    state: RuntimeState,
    tool_descriptions: str,
    agent_descriptions: str,
    skill_descriptions: str,
    memory_context: str,
    skill_prompt_addition: str = "",
    max_batch_size: int = 5,
) -> str:
    """
    Build the system prompt for the planner LLM.

    Delegates the heavy lifting to ``a2a.orchestrator.prompts.planner_prompts``.
    The runtime here only assembles the dynamic context (iteration number,
    applied skills, optional final-answer data render).
    """
    from a2a.orchestrator.prompts.planner_prompts import build_planner_prompt

    context = state.get_context_for_planner()

    # Optional final-answer data render — only included when the planner
    # actually has gathered information. Keeps DECISION-mode prompts compact.
    context_render_for_final = ""
    has_useful_results = bool(state.tool_results) or any(
        r.get("success") for r in state.agent_results.values()
    )
    if has_useful_results and state.context_manager and state.agent_context:
        try:
            context_render_for_final = state.context_manager.render_for_final_llm(
                state.agent_context
            )
        except Exception:
            context_render_for_final = ""

    # Session history summary for follow-up resolution
    session_history_summary = ""
    if state.session_history:
        try:
            from a2a.database import get_session_manager

            session_history_summary = get_session_manager().create_context_summary(
                state.session_history
            )
        except Exception:
            session_history_summary = (
                f"Previous conversation ({len(state.session_history)} messages)."
            )

    return build_planner_prompt(
        user_query=state.user_query,
        tool_descriptions=tool_descriptions,
        agent_descriptions=agent_descriptions,
        skill_descriptions=skill_descriptions,
        memory_context=memory_context,
        iteration=context["iteration"],
        task_summary=context["task_graph"],
        applied_skills=list(state.skill_results.keys()),
        skill_prompt_addition=skill_prompt_addition,
        intent=getattr(state, "intent", None),
        intent_domain=getattr(state, "intent_domain", None),
        complexity=getattr(state, "complexity", None),
        matched_skill=getattr(state, "matched_skill", None),
        context_render_for_final=context_render_for_final,
        session_history_summary=session_history_summary,
        max_batch_size=max_batch_size,
    )


class Planner:
    """
    LLM-based planner that produces a PlannerDecision each iteration.

    Has access to:
    - RuntimeState (query, observations, results)
    - Tool schemas (from ToolManager)
    - Agent schemas (from AgentManager)
    - Skill schemas (from SkillManager)
    - Context (from ContextManager — ranked, deduped, token-budgeted)

    Uses get_instructor_client(json_mode=True) from model_factory,
    which reads the active ModelConfig ContextVar (dynamic per-request)
    or falls back to environment variables.
    """

    async def think(
        self,
        state: RuntimeState,
        tool_descriptions: str,
        agent_descriptions: str,
        skill_descriptions: str,
        memory_context: str,
        skill_prompt_addition: str = "",
        max_batch_size: int = 5,
    ) -> PlannerDecision:
        """
        Produce a PlannerDecision based on current state.

        This is called each iteration of the loop executor.
        Supports single actions and batch (parallel) actions.
        """
        # Fresh client every call — reads ContextVar for dynamic model config
        client, model_name, extra_kwargs = get_instructor_client(json_mode=True)

        system_prompt = _build_planner_system_prompt(
            state=state,
            tool_descriptions=tool_descriptions,
            agent_descriptions=agent_descriptions,
            skill_descriptions=skill_descriptions,
            memory_context=memory_context,
            skill_prompt_addition=skill_prompt_addition,
            max_batch_size=max_batch_size,
        )

        logger.info(
            "Planner thinking (iteration %d, model=%s)...",
            state.iteration,
            model_name,
        )

        try:
            import asyncio
            planner_max_tokens = int(os.getenv("PLANNER_MAX_TOKENS", "4096"))
            result: PlannerOutput = await asyncio.to_thread(
                client.chat.completions.create,
                model=model_name,
                response_model=PlannerOutput,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": state.user_query},
                ],
                temperature=0,
                max_tokens=planner_max_tokens,
                **extra_kwargs,
            )
        except Exception as exc:
            logger.error("Planner LLM call failed: %s", exc)
            # Fallback: produce a final answer indicating failure
            return PlannerDecision(
                action=ActionType.FINAL_ANSWER,
                reasoning=f"Planner failed: {exc}",
                answer=(
                    "I ran into an internal error while processing your "
                    "request. Please try again, and if it keeps happening "
                    "let me know what you were asking so I can help."
                ),
                metadata={"answer_mode": "conversational"},
            )

        logger.info(
            "Planner decided: action=%s, reasoning=%s",
            result.action,
            result.reasoning,
        )

        return self._parse_output(result)

    def _parse_output(self, output: PlannerOutput) -> PlannerDecision:
        """Convert structured LLM output to PlannerDecision."""
        action_str = output.action.lower().strip()

        # Build the metadata dict once — attached to every decision so the
        # runtime can update RuntimeState classification fields.
        metadata: Dict[str, Any] = {
            "intent": output.intent,
            "intent_domain": output.intent_domain,
            "intent_entity": output.intent_entity,
            "intent_action": output.intent_action,
            "complexity": output.complexity,
            "intent_category": output.intent_category,
            "should_pass_history": output.should_pass_history,
            "detected_language": output.detected_language,
            "matched_skill": output.matched_skill,
            "needs_clarification": output.needs_clarification,
            "clarification_reason": output.clarification_reason,
            "answer_mode": output.answer_mode,
        }

        def _wrap(decision: PlannerDecision) -> PlannerDecision:
            decision.metadata = metadata
            return decision

        # Normalize common LLM variations:
        # "tool_calls" → "tool_call", "agent_calls" → "agent_call"
        action_map = {
            "tool_calls": "tool_call",
            "tools_call": "tool_call",
            "call_tool": "tool_call",
            "agent_calls": "agent_call",
            "agents_call": "agent_call",
            "call_agent": "agent_call",
            "skill_calls": "skill_call",
            "final": "final_answer",
            "answer": "final_answer",
            "done": "final_answer",
        }
        action_str = action_map.get(action_str, action_str)

        if action_str == "tool_call":
            # Check for batch tool calls first
            if output.tool_calls and len(output.tool_calls) > 0:
                batch = [
                    {"tool_name": tc.tool_name, "tool_args": tc.tool_args}
                    for tc in output.tool_calls
                ]
                # Single-item batch → treat as single call
                if len(batch) == 1:
                    return _wrap(PlannerDecision(
                        action=ActionType.TOOL_CALL,
                        reasoning=output.reasoning,
                        tool_name=batch[0]["tool_name"],
                        tool_args=batch[0]["tool_args"],
                    ))
                return _wrap(PlannerDecision(
                    action=ActionType.TOOL_CALL,
                    reasoning=output.reasoning,
                    batch_tool_calls=batch,
                ))
            # Single tool call (backward compat)
            if output.tool_name:
                return _wrap(PlannerDecision(
                    action=ActionType.TOOL_CALL,
                    reasoning=output.reasoning,
                    tool_name=output.tool_name,
                    tool_args=output.tool_args or {},
                ))

        if action_str == "agent_call":
            # Check for batch agent calls first
            if output.agent_calls and len(output.agent_calls) > 0:
                batch = [
                    {"agent_name": ac.agent_name, "agent_goal": ac.agent_goal}
                    for ac in output.agent_calls
                ]
                if len(batch) == 1:
                    return _wrap(PlannerDecision(
                        action=ActionType.AGENT_CALL,
                        reasoning=output.reasoning,
                        agent_name=batch[0]["agent_name"],
                        agent_goal=batch[0]["agent_goal"],
                    ))
                return _wrap(PlannerDecision(
                    action=ActionType.AGENT_CALL,
                    reasoning=output.reasoning,
                    batch_agent_calls=batch,
                ))
            # Single agent call (backward compat)
            if output.agent_name:
                return _wrap(PlannerDecision(
                    action=ActionType.AGENT_CALL,
                    reasoning=output.reasoning,
                    agent_name=output.agent_name,
                    agent_goal=output.agent_goal or "",
                ))

        if action_str == "skill_call" and output.skill_name:
            return _wrap(PlannerDecision(
                action=ActionType.SKILL_CALL,
                reasoning=output.reasoning,
                skill_name=output.skill_name,
            ))

        if action_str == "final_answer":
            return _wrap(PlannerDecision(
                action=ActionType.FINAL_ANSWER,
                reasoning=output.reasoning,
                answer=output.answer or "",
            ))

        # Fallback: if action doesn't match, treat as final answer
        logger.warning("Unrecognized planner action '%s', treating as final_answer", action_str)
        return _wrap(PlannerDecision(
            action=ActionType.FINAL_ANSWER,
            reasoning=output.reasoning,
            answer=output.answer or output.reasoning,
        ))

    async def stream_final_answer(
        self,
        state: RuntimeState,
        tool_descriptions: str,
        agent_descriptions: str,
        skill_descriptions: str,
        memory_context: str,
        skill_prompt_addition: str = "",
        max_batch_size: int = 5,
    ):
        """
        Stream the final answer token-by-token using a raw LLM completion.

        Uses a SLIM prompt that contains only what's needed to write the
        user-facing answer (role, formatting rules, evidence, query).
        Deliberately excludes all decision-mode content (tools, agents,
        classification schema, JSON output instructions) to prevent the
        model from emitting structured JSON instead of prose.

        Yields:
            str: Individual token chunks as they are produced by the LLM.
        """
        from a2a.shared.model_factory import get_streaming_completion
        from a2a.orchestrator.prompts.planner_prompts import build_streaming_final_prompt

        # Gather the evidence the model needs to write the answer
        context_render_for_final = ""
        has_useful_results = bool(state.tool_results) or any(
            r.get("success") for r in state.agent_results.values()
        )
        if has_useful_results and state.context_manager and state.agent_context:
            try:
                context_render_for_final = state.context_manager.render_for_final_llm(
                    state.agent_context
                )
            except Exception:
                context_render_for_final = ""

        # Session history for follow-up awareness
        session_history_summary = ""
        if state.session_history:
            try:
                from a2a.database import get_session_manager
                session_history_summary = get_session_manager().create_context_summary(
                    state.session_history
                )
            except Exception:
                session_history_summary = ""

        detected_language = getattr(state, "detected_language", "English") or "English"

        system_prompt = build_streaming_final_prompt(
            user_query=state.user_query,
            context_render_for_final=context_render_for_final,
            session_history_summary=session_history_summary,
            memory_context=memory_context,
            detected_language=detected_language,
        )

        planner_max_tokens = int(os.getenv("PLANNER_MAX_TOKENS", "4096"))

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state.user_query},
        ]

        logger.info("Streaming final answer (slim prompt, no JSON priming)...")

        async for token in get_streaming_completion(
            messages=messages,
            temperature=0,
            max_tokens=planner_max_tokens,
        ):
            yield token
