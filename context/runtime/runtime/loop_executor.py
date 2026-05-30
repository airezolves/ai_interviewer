"""
Loop Executor — Think, Act, Observe cycle.

Runs the core execution loop:
1. Call Planner to decide next action
2. Detect action type (tool / agent / skill / final)
3. Execute the action via the appropriate manager
4. Store observation in memory
5. Repeat until done or max iterations

The loop executor does NOT reason — the Planner does.
The loop executor does NOT choose actions — it dispatches them.
"""

from __future__ import annotations

import asyncio
import json as _json
import logging
import time
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from a2a.orchestrator.runtime.state import (
    ActionType,
    PlannerDecision,
    RuntimeState,
    StepResult,
    StepStatus,
)
from a2a.orchestrator.runtime.planner import Planner
from a2a.orchestrator.runtime.tool_manager import ToolManager
from a2a.orchestrator.runtime.agent_manager import AgentManager
from a2a.orchestrator.runtime.skill_manager import SkillManager
from a2a.orchestrator.runtime.memory_store import MemoryStore
from a2a.orchestrator.context_manager import ContextManager
from a2a.orchestrator.context_manager.models import ToolCallRecord
from a2a.orchestrator.config import (
    INPUT_SUMMARY_CHARS,
    OUTPUT_SUMMARY_CHARS,
    RESULT_PREVIEW_CHARS,
    GOAL_PREVIEW_CHARS,
    RUNTIME_MAX_TOOL_RETRIES,
    RUNTIME_TOOL_TIMEOUT,
    RUNTIME_AGENT_TIMEOUT,
    LARGE_OUTPUT_THRESHOLD,
)

logger = logging.getLogger("runtime.loop_executor")

# ── Fallback answers for force-stop paths ──
# These are USER-FACING strings (the planner no longer rewrites them through
# a separate synthesizer LLM call). Keep them short, friendly, and free of
# internal terminology (no "tool", "agent", "iteration", "step N").
from a2a.orchestrator.prompts.planner_prompts import (
    FALLBACK_COLLECTED as _ANSWER_COLLECTED,
    FALLBACK_TOOLS_UNAVAILABLE as _ANSWER_TOOLS_UNAVAILABLE,
    FALLBACK_AGENTS_UNAVAILABLE as _ANSWER_AGENTS_UNAVAILABLE,
    FALLBACK_MAX_ITERATIONS as _ANSWER_MAX_ITERATIONS,
)


def _is_large_output(result: str) -> bool:
    """Check if a tool result exceeds the large output threshold."""
    return isinstance(result, str) and len(result) > LARGE_OUTPUT_THRESHOLD


class LoopExecutor:
    """
    Executes the Think -> Act -> Observe loop.

    Components:
    - Planner: LLM reasoning (THINK)
    - ToolManager: MCP tool execution (ACT)
    - AgentManager: A2A agent execution (ACT)
    - SkillManager: Workflow presets (ACT - modifies state)
    - MemoryStore: Observation storage (OBSERVE)
    """

    def __init__(
        self,
        planner: Planner,
        tool_manager: ToolManager,
        agent_manager: AgentManager,
        skill_manager: SkillManager,
        memory: MemoryStore,
        context_manager: ContextManager,
        event_callback: Optional[Callable] = None,
        initial_skill_prompt: str = "",
        max_batch_size: int = 5,
    ) -> None:
        self._planner = planner
        self._tool_manager = tool_manager
        self._agent_manager = agent_manager
        self._skill_manager = skill_manager
        self._memory = memory
        self._context_manager = context_manager
        self._event_callback = event_callback
        self._skill_prompt_addition: str = initial_skill_prompt
        self._max_batch_size: int = max_batch_size

        # ── Tool Failure Tracking ──
        # Per-tool consecutive failure count: tool_name -> int
        self._tool_error_counts: Dict[str, int] = {}
        # Dedup tracking: "tool_name|sorted_args_json" -> count
        self._tool_call_history: Dict[str, int] = {}
        # Structured failure log: list of dicts for planner feedback
        self._tool_failures: List[Dict[str, Any]] = []
        # Consecutive blocked iterations (planner ignoring block signals)
        self._consecutive_blocked: int = 0
        # Consecutive planner LLM failures — force-stop after MAX_PLANNER_FAILURES
        self._consecutive_planner_failures: int = 0

        # ── Text Explorer (in-process, lazy-init) ──
        self._text_processor = None
        self._data_store = None

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit a streaming event via callback."""
        if self._event_callback:
            try:
                await self._event_callback(event_type, data)
            except Exception as exc:
                logger.warning("Event callback failed for %s: %s", event_type, exc)

    async def _emit_answer_tokens(self, text: str) -> None:
        """
        Emit a complete text as runtime_answer_token events for SSE streaming.

        Called from ALL paths that set state.final_answer directly (errors,
        fallbacks, force-stops) so the frontend always receives token events
        before the final response event.
        """
        if not self._event_callback or not text:
            return
        # Emit the text as a single token event (it's already complete text,
        # not being generated incrementally by an LLM)
        await self._emit_event("runtime_answer_token", {"token": text})

    def _get_text_processor(self):
        """Lazy-init the text processing components (in-process, no HTTP)."""
        if self._text_processor is None:
            try:
                from a2a.agents.text_explorer.storage import DataStore
                from a2a.agents.text_explorer.tools import TextExplorerTools
                from a2a.agents.text_explorer.processor import TextProcessor

                self._data_store = DataStore()
                tools = TextExplorerTools(self._data_store)
                self._text_processor = TextProcessor(self._data_store, tools)
                logger.info("TextProcessor initialized (in-process)")
            except Exception as exc:
                logger.warning("Failed to init TextProcessor: %s", exc)
        return self._text_processor

    async def _handle_large_output(
        self,
        result: str,
        tool_name: str,
        user_query: str,
    ) -> str:
        """
        Intercept large tool outputs and process via TextProcessor in-process.

        In-process is the right call here: the data is already in memory,
        there's no serialization cost, and no network hop. TextProcessor is
        a pure data-transformation library, not an external capability.
        """
        processor = self._get_text_processor()
        if processor is None:
            logger.warning(
                "TextProcessor unavailable — truncating large output from %s (%d chars)",
                tool_name, len(result),
            )
            return result[:LARGE_OUTPUT_THRESHOLD] + f"\n\n[TRUNCATED — original {len(result):,} chars]"

        try:
            await self._emit_event("compacting_start", {
                "tool": tool_name,
                "original_size": len(result),
                "threshold": LARGE_OUTPUT_THRESHOLD,
            })

            # Store in shared DataStore (zero-copy, already in memory)
            data_ref = await self._data_store.store(
                content=result,
                data_type="tool_output",
                source=tool_name,
            )

            # Process directly — no HTTP, no serialization
            processed = await processor.process(
                data_ref=data_ref,
                user_query=user_query,
                goal=f"Process large output from tool '{tool_name}' to answer: {user_query}",
                mode="auto",
            )

            if processed.get("type") == "error":
                logger.warning(
                    "TextProcessor returned error for %s: %s — truncating",
                    tool_name, processed.get("content", ""),
                )
                return result[:LARGE_OUTPUT_THRESHOLD] + f"\n\n[TRUNCATED — original {len(result):,} chars]"

            content = processed.get("content", "")
            if not content:
                logger.warning("TextProcessor returned empty content for %s — truncating", tool_name)
                return result[:LARGE_OUTPUT_THRESHOLD] + f"\n\n[TRUNCATED — original {len(result):,} chars]"

            metadata = processed.get("metadata", {})
            compact = (
                f"[PROCESSED BY TEXT EXPLORER — Original: {len(result):,} chars]\n\n"
                f"{content}"
            )

            await self._emit_event("compacting_end", {
                "tool": tool_name,
                "original_size": len(result),
                "processed_size": len(compact),
                "mode": metadata.get("processing_mode", "auto"),
                "duration": metadata.get("duration_seconds", 0),
                "result": compact,
            })

            logger.info(
                "TextProcessor processed %s in-process: %d → %d chars (mode=%s, %.1fs)",
                tool_name, len(result), len(compact),
                metadata.get("processing_mode", "?"),
                metadata.get("duration_seconds", 0),
            )

            # Clean up DataStore to prevent memory leak across requests
            if self._data_store and hasattr(self._data_store, 'delete'):
                try:
                    await self._data_store.delete(data_ref)
                except Exception:
                    pass  # Best-effort cleanup

            return compact

        except Exception as exc:
            logger.error(
                "TextProcessor failed for %s: %s(%s) — truncating",
                tool_name, type(exc).__name__, exc,
            )
            return result[:LARGE_OUTPUT_THRESHOLD] + f"\n\n[TRUNCATED — original {len(result):,} chars]"

    async def step(self, state: RuntimeState) -> bool:
        """
        Execute a single iteration of the loop.

        Returns True if the loop should continue, False if done.
        """
        state.iteration += 1
        logger.info(
            "--- Loop iteration %d/%d ---",
            state.iteration,
            state.max_iterations,
        )

        if state.iteration > state.max_iterations:
            logger.warning("Max iterations reached (%d)", state.max_iterations)
            state.done = True

            # Instead of a canned fallback, ask the planner to synthesize a
            # proper final answer from whatever data has been collected so far.
            tool_descriptions = self._tool_manager.get_tool_descriptions()
            agent_descriptions = self._agent_manager.get_agent_descriptions()
            skill_descriptions = self._skill_manager.get_skill_descriptions()

            if state.agent_context and self._context_manager:
                memory_context = self._context_manager.render_for_planner(state.agent_context)
            else:
                memory_context = self._memory.get_context_summary()

            failure_context = self._build_failure_context_for_planner()
            if failure_context:
                memory_context += failure_context

            if self._event_callback:
                await self._emit_event("runtime_final", {
                    "iteration": state.iteration,
                    "has_answer": True,
                    "answer_mode": getattr(state, "answer_mode", None),
                    "streaming": True,
                    "reason": "max_iterations",
                })

                streamed_answer = []
                try:
                    async for token in self._planner.stream_final_answer(
                        state=state,
                        tool_descriptions=tool_descriptions,
                        agent_descriptions=agent_descriptions,
                        skill_descriptions=skill_descriptions,
                        memory_context=memory_context,
                        skill_prompt_addition=self._skill_prompt_addition,
                        max_batch_size=self._max_batch_size,
                    ):
                        streamed_answer.append(token)
                        await self._emit_event("runtime_answer_token", {
                            "token": token,
                        })

                    state.final_answer = "".join(streamed_answer)
                    logger.info(
                        "Max-iterations final answer streamed: %d tokens, %d chars",
                        len(streamed_answer),
                        len(state.final_answer),
                    )
                except Exception as exc:
                    logger.error("Streaming final answer on max-iterations failed: %s", exc)
                    state.final_answer = _ANSWER_MAX_ITERATIONS
                    await self._emit_answer_tokens(state.final_answer)
            else:
                # Non-streaming: call planner's think() — it should produce FINAL_ANSWER
                # given no remaining iterations. Fall back to canned message on failure.
                try:
                    decision = await self._planner.think(
                        state=state,
                        tool_descriptions=tool_descriptions,
                        agent_descriptions=agent_descriptions,
                        skill_descriptions=skill_descriptions,
                        memory_context=memory_context,
                        skill_prompt_addition=self._skill_prompt_addition,
                        max_batch_size=self._max_batch_size,
                    )
                    state.final_answer = decision.answer or _ANSWER_MAX_ITERATIONS
                except Exception as exc:
                    logger.error("Planner think on max-iterations failed: %s", exc)
                    state.final_answer = _ANSWER_MAX_ITERATIONS

            return False

        # -- THINK: Ask planner for next action --
        await self._emit_event("runtime_think", {
            "iteration": state.iteration,
            "status": "planning",
        })

        tool_descriptions = self._tool_manager.get_tool_descriptions()
        agent_descriptions = self._agent_manager.get_agent_descriptions()
        skill_descriptions = self._skill_manager.get_skill_descriptions()

        # Use context manager's rendered context as primary source for planner.
        # Falls back to legacy memory_context if agent_context is not available.
        if state.agent_context and self._context_manager:
            memory_context = self._context_manager.render_for_planner(state.agent_context)
        else:
            memory_context = self._memory.get_context_summary()

        # Inject structured failure context so planner can adapt strategy
        failure_context = self._build_failure_context_for_planner()
        if failure_context:
            memory_context += failure_context

        decision = await self._planner.think(
            state=state,
            tool_descriptions=tool_descriptions,
            agent_descriptions=agent_descriptions,
            skill_descriptions=skill_descriptions,
            memory_context=memory_context,
            skill_prompt_addition=self._skill_prompt_addition,
            max_batch_size=self._max_batch_size,
        )

        # Track planner failures for early termination
        from a2a.orchestrator.config import MAX_PLANNER_FAILURES
        if decision.action == ActionType.FINAL_ANSWER and decision.answer and \
                "internal error" in (decision.answer or "").lower():
            self._consecutive_planner_failures += 1
            if self._consecutive_planner_failures >= MAX_PLANNER_FAILURES:
                logger.error("Planner failed %d consecutive times — force stopping", MAX_PLANNER_FAILURES)
                state.done = True
                state.final_answer = decision.answer
                await self._emit_answer_tokens(state.final_answer)
                return False
        else:
            self._consecutive_planner_failures = 0

        # Merge planner-produced classification metadata into runtime state.
        # The planner now owns intent/skill/clarification fields directly
        # (the dedicated intent_analysis node has been removed).
        try:
            state.update_metadata_from_decision(decision)
        except Exception as exc:
            logger.debug("Metadata propagation skipped: %s", exc)

        # Update context manager's plan slot with planner reasoning
        if state.agent_context and self._context_manager and decision.reasoning:
            state.agent_context = self._context_manager.update_plan(
                state.agent_context, decision.reasoning
            )

        # Determine target name for event
        target = (
            decision.tool_name
            or decision.agent_name
            or decision.skill_name
            or ("batch_tools" if decision.batch_tool_calls else None)
            or ("batch_agents" if decision.batch_agent_calls else None)
            or "final"
        )

        await self._emit_event("runtime_decision", {
            "iteration": state.iteration,
            "action": decision.action.value,
            "reasoning": decision.reasoning,
            "target": target,
            "batch_size": (
                len(decision.batch_tool_calls) if decision.batch_tool_calls
                else len(decision.batch_agent_calls) if decision.batch_agent_calls
                else 1
            ),
        })

        # -- ACT: Dispatch based on action type --
        if decision.action == ActionType.TOOL_CALL:
            if decision.batch_tool_calls:
                await self._execute_tool_batch(state, decision)
            else:
                await self._execute_tool(state, decision)
            return True

        if decision.action == ActionType.AGENT_CALL:
            if decision.batch_agent_calls:
                await self._execute_agent_batch(state, decision)
            else:
                await self._execute_agent(state, decision)
            return True

        if decision.action == ActionType.SKILL_CALL:
            skill_name = decision.skill_name or ""
            if skill_name in state.skill_results:
                # Skill already applied — redirect planner to call tools
                logger.warning("Skill '%s' already applied. Injecting redirect observation.", skill_name)
                state.add_observation({
                    "type": "skill_already_applied",
                    "skill": skill_name,
                    "note": (
                        f"Skill '{skill_name}' is ALREADY applied and its knowledge is in your context. "
                        "Do NOT apply it again. You MUST now call the relevant tools to gather actual data."
                    ),
                })
            else:
                await self._execute_skill(state, decision)
            return True

        if decision.action == ActionType.FINAL_ANSWER:
            state.done = True

            # ── Token streaming for final answer ──
            # When an event callback is present (streaming mode), generate
            # the answer via a streaming LLM call and emit tokens in real-time.
            if self._event_callback:
                await self._emit_event("runtime_final", {
                    "iteration": state.iteration,
                    "has_answer": True,
                    "answer_mode": getattr(state, "answer_mode", None),
                    "streaming": True,
                })

                streamed_answer = []
                try:
                    async for token in self._planner.stream_final_answer(
                        state=state,
                        tool_descriptions=tool_descriptions,
                        agent_descriptions=agent_descriptions,
                        skill_descriptions=skill_descriptions,
                        memory_context=memory_context,
                        skill_prompt_addition=self._skill_prompt_addition,
                        max_batch_size=self._max_batch_size,
                    ):
                        streamed_answer.append(token)
                        await self._emit_event("runtime_answer_token", {
                            "token": token,
                        })

                    state.final_answer = "".join(streamed_answer)
                    logger.info(
                        "Streamed final answer: %d tokens, %d chars",
                        len(streamed_answer),
                        len(state.final_answer),
                    )
                except Exception as exc:
                    logger.error("Streaming final answer failed: %s", exc)
                    # Fallback: use the instructor-generated answer
                    state.final_answer = decision.answer or ""
                    await self._emit_answer_tokens(state.final_answer)
                    logger.info("Falling back to instructor-generated answer")
            else:
                # Non-streaming mode: use the instructor answer directly
                state.final_answer = decision.answer or ""
                await self._emit_event("runtime_final", {
                    "iteration": state.iteration,
                    "has_answer": bool(state.final_answer),
                    "answer_mode": getattr(state, "answer_mode", None),
                })

            return False

        # Unknown action — stop loop
        logger.warning("Unknown action type: %s", decision.action)
        state.done = True
        return False

    def _make_dedup_key(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Create a dedup key from tool name + sorted args."""
        return f"{tool_name}|{_json.dumps(tool_args, sort_keys=True, default=str)}"

    def _build_failure_context_for_planner(self) -> str:
        """Build a structured failure summary for the planner's context."""
        if not self._tool_failures:
            return ""
        lines = ["\n## TOOL FAILURES (use this to decide next action)"]
        for f in self._tool_failures[-5:]:  # last 5 failures
            lines.append(
                f"- tool: {f['tool']}, input: {str(f['input'])[:120]}, "
                f"error_type: {f['error_type']}, message: {f['message'][:150]}, "
                f"attempt: {f['attempt']}/{RUNTIME_MAX_TOOL_RETRIES}, "
                f"retryable: {f['retryable']}"
            )
        lines.append(
            "→ Do NOT retry with identical inputs. Modify input, try alternative tool, or give final_answer."
        )
        return "\n".join(lines)

    def _is_duplicate_call(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """Check if this exact tool+args has already been called 2+ times."""
        key = self._make_dedup_key(tool_name, tool_args)
        return self._tool_call_history.get(key, 0) >= 2

    def _record_call(self, tool_name: str, tool_args: Dict[str, Any]) -> int:
        """Record a tool call and return the call count."""
        key = self._make_dedup_key(tool_name, tool_args)
        self._tool_call_history[key] = self._tool_call_history.get(key, 0) + 1
        # Prevent unbounded growth (cap at 100 unique call signatures)
        if len(self._tool_call_history) > 100:
            oldest_keys = list(self._tool_call_history.keys())[:-100]
            for k in oldest_keys:
                del self._tool_call_history[k]
        return self._tool_call_history[key]

    def _record_failure(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        error_msg: str,
        error_type: str = "EXECUTION_ERROR",
        retryable: bool = True,
    ) -> Dict[str, Any]:
        """Record a tool failure and return the structured failure record."""
        count = self._tool_error_counts.get(tool_name, 0) + 1
        self._tool_error_counts[tool_name] = count

        failure = {
            "tool": tool_name,
            "input": tool_args,
            "error_type": error_type,
            "message": error_msg,
            "attempt": count,
            "retryable": retryable and count < RUNTIME_MAX_TOOL_RETRIES,
        }
        self._tool_failures.append(failure)
        # Keep only last 10 failures to prevent unbounded growth
        if len(self._tool_failures) > 10:
            self._tool_failures = self._tool_failures[-10:]
        return failure

    def _make_tool_response(
        self,
        success: bool,
        data: Any = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        retryable: bool = False,
    ) -> Dict[str, Any]:
        """Build a standardized tool response."""
        resp: Dict[str, Any] = {"success": success, "data": data}
        if not success:
            resp["error"] = {
                "type": error_type or "UNKNOWN_ERROR",
                "message": error_message or "Unknown error",
                "retryable": retryable,
            }
        return resp

    async def _record_and_emit_tool_error(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        step_id: str,
        state: RuntimeState,
        error_msg: str,
        error_type: str,
        retryable: bool,
        duration_ms: float,
        is_batch: bool,
    ) -> None:
        """Record a tool failure, emit events, and add observations — shared by all error paths."""
        failure = self._record_failure(
            tool_name, tool_args,
            error_msg=error_msg, error_type=error_type, retryable=retryable,
        )
        step_result = StepResult(
            step_id=step_id, action=ActionType.TOOL_CALL, name=tool_name,
            success=False, error=error_msg, duration_ms=duration_ms,
        )
        state.task_graph.mark_failed(step_id, step_result)
        self._memory.add_tool_result(
            tool_name=tool_name, args=tool_args,
            result=f"Error: {error_msg}", success=False, step_id=step_id,
        )
        if state.agent_context and self._context_manager:
            state.agent_context = self._context_manager.record_error(
                state.agent_context, f"{tool_name}: {error_msg}"
            )
            state.agent_context = self._context_manager.record_tool_call(
                state.agent_context,
                ToolCallRecord(
                    tool_name=tool_name,
                    input_summary=str(tool_args)[:INPUT_SUMMARY_CHARS],
                    output_summary=f"ERROR[{error_type}]: {error_msg}"[:OUTPUT_SUMMARY_CHARS],
                    success=False,
                ),
            )
        state.add_observation({
            "type": "tool_failure",
            "tool": tool_name,
            "response": self._make_tool_response(
                success=False, error_type=error_type,
                error_message=error_msg, retryable=failure["retryable"],
            ),
            "failure": failure,
            "message": (
                f"Tool '{tool_name}' failed with {error_type}: {error_msg[:150]} "
                f"(attempt {failure['attempt']}/{RUNTIME_MAX_TOOL_RETRIES}). "
                + (
                    "Retry with modified input or try alternative."
                    if failure["retryable"]
                    else "NOT retryable — move on."
                )
            ),
        })
        await self._emit_event("runtime_tool_end", {
            "step_id": step_id, "tool": tool_name,
            "success": False, "error": error_msg,
            "error_type": error_type, "retryable": failure["retryable"],
            "attempt": failure["attempt"], "duration_ms": round(duration_ms, 1),
            **({"batch": True} if is_batch else {}),
        })
        logger.error(
            "Tool %s failed [%s] (attempt %d/%d, retryable=%s): %s",
            tool_name, error_type, failure["attempt"], RUNTIME_MAX_TOOL_RETRIES,
            failure["retryable"], error_msg,
        )

    async def _execute_one_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        state: RuntimeState,
        *,
        is_batch: bool = False,
    ) -> None:
        """
        Core tool execution — shared by both single and batch paths.

        Caller is responsible for dedup/exhaustion checks and recording the call.
        This method owns: step creation, timeout, empty-result check,
        large-output handling, success/failure recording, events, observations.
        """
        step_id = state.task_graph.add_step(
            action=ActionType.TOOL_CALL,
            name=tool_name,
            goal=f"{'[batch] ' if is_batch else ''}Call {tool_name} with {str(tool_args)[:INPUT_SUMMARY_CHARS]}",
        )
        state.task_graph.mark_in_progress(step_id)

        await self._emit_event("runtime_tool_start", {
            "step_id": step_id,
            "tool": tool_name,
            "args": tool_args,
            **({"batch": True} if is_batch else {}),
        })

        start_time = time.monotonic()
        try:
            result = await asyncio.wait_for(
                self._tool_manager.call_tool(tool_name, tool_args),
                timeout=RUNTIME_TOOL_TIMEOUT,
            )
            duration_ms = (time.monotonic() - start_time) * 1000

            # ── Empty result check ──
            is_empty = (
                result is None
                or (isinstance(result, str) and not result.strip())
                or result == "[]"
                or result == "{}"
            )
            if is_empty:
                failure = self._record_failure(
                    tool_name, tool_args,
                    error_msg="Tool returned empty/null result",
                    error_type="EMPTY_RESULT",
                    retryable=True,
                )
                step_result = StepResult(
                    step_id=step_id, action=ActionType.TOOL_CALL, name=tool_name,
                    success=False, error="Empty result", duration_ms=duration_ms,
                )
                state.task_graph.mark_failed(step_id, step_result)
                self._memory.add_tool_result(
                    tool_name=tool_name, args=tool_args,
                    result="Empty result", success=False, step_id=step_id,
                )
                if state.agent_context and self._context_manager:
                    state.agent_context = self._context_manager.record_tool_call(
                        state.agent_context,
                        ToolCallRecord(
                            tool_name=tool_name,
                            input_summary=str(tool_args)[:INPUT_SUMMARY_CHARS],
                            output_summary="EMPTY_RESULT",
                            success=False,
                        ),
                    )
                state.add_observation({
                    "type": "tool_failure",
                    "tool": tool_name,
                    "response": self._make_tool_response(
                        success=False,
                        error_type="EMPTY_RESULT",
                        error_message="Tool returned empty/null result",
                        retryable=failure["retryable"],
                    ),
                    "failure": failure,
                    "message": (
                        f"Tool '{tool_name}' returned empty result "
                        f"(attempt {failure['attempt']}/{RUNTIME_MAX_TOOL_RETRIES}). "
                        + (
                            "Retry with DIFFERENT/broader parameters."
                            if failure["retryable"]
                            else "Retries exhausted — use collected data or try alternative tool."
                        )
                    ),
                })
                await self._emit_event("runtime_tool_end", {
                    "step_id": step_id, "tool": tool_name,
                    "success": False, "error": "Empty result",
                    "duration_ms": round(duration_ms, 1),
                    **({"batch": True} if is_batch else {}),
                })
                logger.warning(
                    "Tool %s returned empty (attempt %d/%d)",
                    tool_name, failure["attempt"], RUNTIME_MAX_TOOL_RETRIES,
                )
                return

            # ── Large output interception ──
            if _is_large_output(result):
                logger.info(
                    "Large output from %s: %d chars (threshold=%d). Delegating to Text Explorer.",
                    tool_name, len(result), LARGE_OUTPUT_THRESHOLD,
                )
                result = await self._handle_large_output(result, tool_name, state.user_query)

            # ── Success path ──
            step_result = StepResult(
                step_id=step_id, action=ActionType.TOOL_CALL, name=tool_name,
                success=True, result=result, duration_ms=duration_ms,
            )
            state.task_graph.mark_completed(step_id, step_result)
            self._tool_error_counts.pop(tool_name, None)

            call_key = f"{tool_name}_{step_id}"
            state.store_tool_result(call_key, result)
            self._memory.add_tool_result(
                tool_name=tool_name, args=tool_args,
                result=result, success=True, step_id=step_id,
            )
            if state.agent_context and self._context_manager:
                state.agent_context = await self._context_manager.process_tool_output(
                    state.agent_context, result, tool_name
                )
                state.agent_context = self._context_manager.record_tool_call(
                    state.agent_context,
                    ToolCallRecord(
                        tool_name=tool_name,
                        input_summary=str(tool_args)[:INPUT_SUMMARY_CHARS],
                        output_summary=self._context_manager.summarize_output(result, tool_name),
                        success=True,
                    ),
                )
            state.add_observation({
                "type": "tool_result",
                "tool": tool_name,
                "success": True,
                "step_id": step_id,
            })
            await self._emit_event("runtime_tool_end", {
                "step_id": step_id, "tool": tool_name,
                "success": True, "duration_ms": round(duration_ms, 1),
                "result_preview": (
                    result[:RESULT_PREVIEW_CHARS]
                    if isinstance(result, str)
                    else str(result)[:RESULT_PREVIEW_CHARS]
                ),
                **({"batch": True} if is_batch else {}),
            })
            logger.info(
                "Tool %s completed in %.1fms (%d chars)%s",
                tool_name, duration_ms,
                len(result) if isinstance(result, str) else 0,
                " [batch]" if is_batch else "",
            )

        except asyncio.TimeoutError:
            duration_ms = (time.monotonic() - start_time) * 1000
            await self._record_and_emit_tool_error(
                tool_name, tool_args, step_id, state,
                error_msg=f"Tool timed out after {RUNTIME_TOOL_TIMEOUT}s",
                error_type="TIMEOUT", retryable=True,
                duration_ms=duration_ms, is_batch=is_batch,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            error_msg = str(exc)
            error_type = "EXECUTION_ERROR"
            retryable = True
            if "not found" in error_msg.lower() or "404" in error_msg:
                error_type, retryable = "NOT_FOUND", False
            elif "permission" in error_msg.lower() or "403" in error_msg:
                error_type, retryable = "PERMISSION_DENIED", False
            elif "invalid" in error_msg.lower() or "validation" in error_msg.lower():
                error_type = "INVALID_INPUT"
            await self._record_and_emit_tool_error(
                tool_name, tool_args, step_id, state,
                error_msg=error_msg, error_type=error_type, retryable=retryable,
                duration_ms=duration_ms, is_batch=is_batch,
            )

    async def _execute_tool(
        self, state: RuntimeState, decision: PlannerDecision
    ) -> None:
        """Execute a tool call with standardized response, dedup, and retry tracking."""
        tool_name = decision.tool_name or ""
        tool_args = decision.tool_args or {}

        # ── 1. Dedup check: block identical calls ──
        if self._is_duplicate_call(tool_name, tool_args):
            self._consecutive_blocked += 1
            logger.warning(
                "BLOCKED duplicate call: %s with identical args (blocked %d consecutive times)",
                tool_name, self._consecutive_blocked,
            )
            if self._consecutive_blocked >= 2:
                # Planner is stuck in a loop — force final answer
                logger.warning("Planner stuck in retry loop. Forcing final_answer.")
                state.done = True
                state.final_answer = _ANSWER_COLLECTED
                await self._emit_answer_tokens(state.final_answer)
                return
            state.add_observation({
                "type": "tool_blocked_duplicate",
                "tool": tool_name,
                "message": (
                    f"BLOCKED: Tool '{tool_name}' was already called with identical arguments "
                    f"and returned the same result. You MUST either: "
                    f"(1) modify the input parameters, (2) use a different tool, "
                    f"or (3) give final_answer with collected data. "
                    f"WARNING: If you try again, execution will be force-stopped."
                ),
            })
            return

        # ── 2. Exhaustion check: tool has failed too many times ──
        consecutive_fails = self._tool_error_counts.get(tool_name, 0)
        if consecutive_fails >= RUNTIME_MAX_TOOL_RETRIES:
            self._consecutive_blocked += 1
            logger.warning(
                "BLOCKED exhausted tool: %s (failed %d/%d times)",
                tool_name, consecutive_fails, RUNTIME_MAX_TOOL_RETRIES,
            )
            if self._consecutive_blocked >= 2:
                logger.warning("Planner stuck retrying exhausted tools. Forcing final_answer.")
                state.done = True
                state.final_answer = _ANSWER_TOOLS_UNAVAILABLE
                await self._emit_answer_tokens(state.final_answer)
                return
            state.add_observation({
                "type": "tool_exhausted",
                "tool": tool_name,
                "message": (
                    f"Tool '{tool_name}' has failed {consecutive_fails} consecutive times "
                    f"and is UNAVAILABLE. Do NOT retry. Use collected data to give final_answer, "
                    f"or try an alternative tool/agent."
                ),
                "failures": [
                    f for f in self._tool_failures if f["tool"] == tool_name
                ][-3:],
            })
            if state.agent_context and self._context_manager:
                state.agent_context = self._context_manager.record_error(
                    state.agent_context,
                    f"Tool '{tool_name}' exhausted after {consecutive_fails} failures",
                )
            return

        # Reset blocked counter — a non-duplicate call was attempted
        self._consecutive_blocked = 0

        # ── 3. Record and execute ──
        self._record_call(tool_name, tool_args)
        await self._execute_one_tool_call(tool_name, tool_args, state, is_batch=False)

    async def _execute_tool_batch(
        self, state: RuntimeState, decision: PlannerDecision
    ) -> None:
        """Execute multiple tool calls in parallel using asyncio.gather."""
        batch = decision.batch_tool_calls or []
        if not batch:
            return

        # Cap batch size
        batch = batch[:self._max_batch_size]

        # Pre-filter: check dedup/exhaustion BEFORE executing any
        executable = []
        blocked_count = 0
        for tc in batch:
            t_name = tc.get("tool_name", "")
            t_args = tc.get("tool_args", {})
            if self._is_duplicate_call(t_name, t_args):
                blocked_count += 1
                logger.warning("BLOCKED duplicate batch call: %s", t_name)
                continue
            if self._tool_error_counts.get(t_name, 0) >= RUNTIME_MAX_TOOL_RETRIES:
                blocked_count += 1
                logger.warning("BLOCKED exhausted tool in batch: %s", t_name)
                continue
            executable.append(tc)

        # ALL items blocked — treat as consecutive block
        if not executable:
            self._consecutive_blocked += 1
            logger.warning(
                "Entire batch blocked (%d items). consecutive_blocked=%d",
                len(batch), self._consecutive_blocked,
            )
            if self._consecutive_blocked >= 2:
                logger.warning("Planner stuck in batch retry loop. Forcing final_answer.")
                state.done = True
                state.final_answer = _ANSWER_COLLECTED
                await self._emit_answer_tokens(state.final_answer)
                return
            state.add_observation({
                "type": "batch_blocked_duplicate",
                "message": (
                    f"ALL {len(batch)} batch tool calls were BLOCKED as duplicates. "
                    f"You already have the data. Give final_answer NOW. "
                    f"WARNING: Next attempt will force-stop execution."
                ),
            })
            return

        # Reset blocked counter — some calls are proceeding
        self._consecutive_blocked = 0

        await self._emit_event("runtime_batch_start", {
            "iteration": state.iteration,
            "type": "tool_call",
            "count": len(executable),
        })

        async def _run_single_tool(tool_call: Dict[str, Any]) -> None:
            t_name = tool_call.get("tool_name", "")
            t_args = tool_call.get("tool_args", {})
            self._record_call(t_name, t_args)
            await self._execute_one_tool_call(t_name, t_args, state, is_batch=True)

        # Execute all tool calls in parallel
        await asyncio.gather(
            *[_run_single_tool(tc) for tc in executable],
            return_exceptions=True,
        )

        await self._emit_event("runtime_batch_end", {
            "iteration": state.iteration,
            "type": "tool_call",
            "count": len(executable),
        })

        logger.info("Batch tool execution completed: %d calls (%d blocked)", len(executable), blocked_count)

    async def _execute_agent(
        self, state: RuntimeState, decision: PlannerDecision
    ) -> None:
        """Execute an agent call with dedup, failure tracking, and force-stop."""
        agent_name = decision.agent_name or ""
        agent_goal = decision.agent_goal or state.user_query
        # Use agent_name as the dedup key (goal is often identical across retries)
        agent_args = {"goal": agent_goal}

        # ── 1. Dedup check: block identical agent calls ──
        if self._is_duplicate_call(agent_name, agent_args):
            self._consecutive_blocked += 1
            logger.warning(
                "BLOCKED duplicate agent call: %s (blocked %d consecutive times)",
                agent_name, self._consecutive_blocked,
            )
            if self._consecutive_blocked >= 2:
                logger.warning("Planner stuck calling same agent. Forcing final_answer.")
                state.done = True
                state.final_answer = _ANSWER_COLLECTED
                await self._emit_answer_tokens(state.final_answer)
                return
            state.add_observation({
                "type": "tool_blocked_duplicate",
                "tool": agent_name,
                "message": (
                    f"BLOCKED: Agent '{agent_name}' was already called with identical goal "
                    f"and returned the same error. You MUST either: "
                    f"(1) use the data you already have to give final_answer, "
                    f"(2) try a different approach, or (3) call a tool instead. "
                    f"WARNING: If you try again, execution will be force-stopped."
                ),
            })
            return

        # ── 2. Exhaustion check: agent has failed too many times ──
        consecutive_fails = self._tool_error_counts.get(agent_name, 0)
        if consecutive_fails >= RUNTIME_MAX_TOOL_RETRIES:
            self._consecutive_blocked += 1
            logger.warning(
                "BLOCKED exhausted agent: %s (failed %d/%d times)",
                agent_name, consecutive_fails, RUNTIME_MAX_TOOL_RETRIES,
            )
            if self._consecutive_blocked >= 2:
                logger.warning("Planner stuck retrying exhausted agent. Forcing final_answer.")
                state.done = True
                state.final_answer = _ANSWER_AGENTS_UNAVAILABLE
                await self._emit_answer_tokens(state.final_answer)
                return
            state.add_observation({
                "type": "tool_exhausted",
                "tool": agent_name,
                "message": (
                    f"Agent '{agent_name}' has failed {consecutive_fails} consecutive times "
                    f"and is UNAVAILABLE. Do NOT call it again. Use collected data to give final_answer, "
                    f"or try a different approach."
                ),
            })
            return

        # Reset blocked counter — a non-duplicate call was attempted
        self._consecutive_blocked = 0

        # ── 3. Record this call ──
        self._record_call(agent_name, agent_args)

        step_id = state.task_graph.add_step(
            action=ActionType.AGENT_CALL,
            name=agent_name,
            goal=agent_goal[:GOAL_PREVIEW_CHARS],
        )
        state.task_graph.mark_in_progress(step_id)

        await self._emit_event("runtime_agent_start", {
            "step_id": step_id,
            "agent": agent_name,
            "goal": agent_goal[:GOAL_PREVIEW_CHARS],
        })

        start_time = time.monotonic()
        try:
            # Build context from previous results
            context = {}
            for k, v in state.tool_results.items():
                context[k] = v[:RESULT_PREVIEW_CHARS] if isinstance(v, str) else v
            for k, v in state.agent_results.items():
                context[k] = v.get("summary", "")[:RESULT_PREVIEW_CHARS] if isinstance(v, dict) else str(v)[:RESULT_PREVIEW_CHARS]

            result = await asyncio.wait_for(
                self._agent_manager.call_agent(
                    agent_name=agent_name,
                    goal=agent_goal,
                    user_query=state.user_query,
                    context=context if context else None,
                ),
                timeout=RUNTIME_AGENT_TIMEOUT,
            )
            duration_ms = (time.monotonic() - start_time) * 1000

            success = result.get("success", False)

            if not success:
                # ── Agent returned failure — track it ──
                error_msg = result.get("summary", "Agent returned failure")
                failure = self._record_failure(
                    agent_name, agent_args,
                    error_msg=error_msg,
                    error_type="AGENT_ERROR",
                    retryable=consecutive_fails + 1 < RUNTIME_MAX_TOOL_RETRIES,
                )
                step_result = StepResult(
                    step_id=step_id,
                    action=ActionType.AGENT_CALL,
                    name=agent_name,
                    success=False,
                    error=error_msg,
                    duration_ms=duration_ms,
                )
                state.task_graph.mark_failed(step_id, step_result)

                state.agent_results[agent_name] = result
                self._memory.add_agent_result(
                    agent_name=agent_name, goal=agent_goal,
                    result=error_msg, success=False, step_id=step_id,
                )
                state.add_observation({
                    "type": "tool_failure",
                    "tool": agent_name,
                    "failure": failure,
                    "message": (
                        f"Agent '{agent_name}' FAILED (attempt {failure['attempt']}/{RUNTIME_MAX_TOOL_RETRIES}): {error_msg[:200]}. "
                        f"{'Do NOT retry with same goal — modify approach or use collected data for final_answer.' if not failure['retryable'] else 'You may retry with a different goal/approach.'}"
                    ),
                })
                await self._emit_event("runtime_agent_end", {
                    "step_id": step_id, "agent": agent_name,
                    "success": False, "error": error_msg[:200],
                    "duration_ms": round(duration_ms, 1),
                })
                logger.info(
                    "Agent %s failed in %.1fms (attempt %d/%d): %s",
                    agent_name, duration_ms, failure["attempt"],
                    RUNTIME_MAX_TOOL_RETRIES, error_msg[:150],
                )
                return

            # ── Success path ──
            step_result = StepResult(
                step_id=step_id,
                action=ActionType.AGENT_CALL,
                name=agent_name,
                success=True,
                result=result.get("summary", ""),
                duration_ms=duration_ms,
            )
            state.task_graph.mark_completed(step_id, step_result)

            # Reset error counter on success
            self._tool_error_counts.pop(agent_name, None)

            state.agent_results[agent_name] = result
            self._memory.add_agent_result(
                agent_name=agent_name, goal=agent_goal,
                result=result.get("summary", ""), success=True, step_id=step_id,
            )
            state.add_observation({
                "type": "agent_result",
                "agent": agent_name,
                "success": True,
                "summary": result.get("summary", "")[:RESULT_PREVIEW_CHARS],
            })

            await self._emit_event("runtime_agent_end", {
                "step_id": step_id, "agent": agent_name,
                "success": True,
                "summary": result.get("summary", "")[:RESULT_PREVIEW_CHARS],
                "duration_ms": round(duration_ms, 1),
            })
            logger.info(
                "Agent %s completed in %.1fms (success)",
                agent_name, duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.monotonic() - start_time) * 1000
            error_msg = f"Agent timed out after {RUNTIME_AGENT_TIMEOUT}s"

            failure = self._record_failure(
                agent_name, agent_args,
                error_msg=error_msg,
                error_type="TIMEOUT",
                retryable=False,
            )
            step_result = StepResult(
                step_id=step_id, action=ActionType.AGENT_CALL, name=agent_name,
                success=False, error=error_msg, duration_ms=duration_ms,
            )
            state.task_graph.mark_failed(step_id, step_result)
            self._memory.add_agent_result(
                agent_name=agent_name, goal=agent_goal,
                result=f"Error: {error_msg}", success=False, step_id=step_id,
            )
            state.add_observation({
                "type": "tool_failure",
                "tool": agent_name,
                "failure": failure,
                "message": (
                    f"Agent '{agent_name}' TIMED OUT after {RUNTIME_AGENT_TIMEOUT}s. "
                    "Do NOT retry — use collected data for final_answer."
                ),
            })
            await self._emit_event("runtime_agent_end", {
                "step_id": step_id, "agent": agent_name,
                "success": False, "error": error_msg,
                "duration_ms": round(duration_ms, 1),
            })
            logger.error("Agent %s timed out after %.0fs", agent_name, RUNTIME_AGENT_TIMEOUT)

        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            error_msg = str(exc)

            failure = self._record_failure(
                agent_name, agent_args,
                error_msg=error_msg,
                error_type="AGENT_EXCEPTION",
                retryable=self._tool_error_counts.get(agent_name, 0) < RUNTIME_MAX_TOOL_RETRIES,
            )

            step_result = StepResult(
                step_id=step_id,
                action=ActionType.AGENT_CALL,
                name=agent_name,
                success=False,
                error=error_msg,
                duration_ms=duration_ms,
            )
            state.task_graph.mark_failed(step_id, step_result)

            self._memory.add_agent_result(
                agent_name=agent_name, goal=agent_goal,
                result=f"Error: {error_msg}", success=False, step_id=step_id,
            )
            state.add_observation({
                "type": "tool_failure",
                "tool": agent_name,
                "failure": failure,
                "message": (
                    f"Agent '{agent_name}' EXCEPTION (attempt {failure['attempt']}/{RUNTIME_MAX_TOOL_RETRIES}): {error_msg[:200]}. "
                    f"Do NOT retry with same approach."
                ),
            })

            await self._emit_event("runtime_agent_end", {
                "step_id": step_id, "agent": agent_name,
                "success": False, "error": error_msg[:200],
                "duration_ms": round(duration_ms, 1),
            })
            logger.error("Agent %s failed: %s", agent_name, error_msg)

    async def _execute_agent_batch(
        self, state: RuntimeState, decision: PlannerDecision
    ) -> None:
        """Execute multiple agent calls in parallel using asyncio.gather."""
        batch = decision.batch_agent_calls or []
        if not batch:
            return

        batch = batch[:self._max_batch_size]

        # Pre-filter: check dedup/exhaustion BEFORE scheduling parallel execution
        executable = []
        blocked_count = 0
        for ac in batch:
            a_name = ac.get("agent_name", "")
            a_args = {"goal": ac.get("agent_goal", state.user_query)}
            if self._is_duplicate_call(a_name, a_args):
                blocked_count += 1
                logger.warning("BLOCKED duplicate batch agent call: %s", a_name)
                continue
            if self._tool_error_counts.get(a_name, 0) >= RUNTIME_MAX_TOOL_RETRIES:
                blocked_count += 1
                logger.warning("BLOCKED exhausted agent in batch: %s", a_name)
                continue
            executable.append(ac)

        if not executable:
            self._consecutive_blocked += 1
            logger.warning(
                "Entire agent batch blocked (%d items). consecutive_blocked=%d",
                len(batch), self._consecutive_blocked,
            )
            if self._consecutive_blocked >= 2:
                logger.warning("Planner stuck in agent batch retry loop. Forcing final_answer.")
                state.done = True
                state.final_answer = _ANSWER_COLLECTED
                await self._emit_answer_tokens(state.final_answer)
                return
            state.add_observation({
                "type": "batch_blocked_duplicate",
                "message": (
                    f"ALL {len(batch)} batch agent calls were BLOCKED as duplicates. "
                    "You already have the data. Give final_answer NOW. "
                    "WARNING: Next attempt will force-stop execution."
                ),
            })
            return

        self._consecutive_blocked = 0

        await self._emit_event("runtime_batch_start", {
            "iteration": state.iteration,
            "type": "agent_call",
            "count": len(executable),
        })

        async def _run_single_agent(agent_call: Dict[str, Any]) -> None:
            single_decision = PlannerDecision(
                action=ActionType.AGENT_CALL,
                reasoning=decision.reasoning,
                agent_name=agent_call.get("agent_name", ""),
                agent_goal=agent_call.get("agent_goal", state.user_query),
            )
            await self._execute_agent(state, single_decision)

        await asyncio.gather(
            *[_run_single_agent(ac) for ac in executable],
            return_exceptions=True,
        )

        await self._emit_event("runtime_batch_end", {
            "iteration": state.iteration,
            "type": "agent_call",
            "count": len(executable),
        })

        logger.info(
            "Batch agent execution completed: %d calls (%d blocked)",
            len(executable), blocked_count,
        )

    async def _execute_skill(
        self, state: RuntimeState, decision: PlannerDecision
    ) -> None:
        """Apply a skill — modifies prompts, does not execute."""
        skill_name = decision.skill_name or ""

        step_id = state.task_graph.add_step(
            action=ActionType.SKILL_CALL,
            name=skill_name,
            goal=f"Apply skill: {skill_name}",
        )
        state.task_graph.mark_in_progress(step_id)

        result = self._skill_manager.apply_skill(skill_name=skill_name)

        # Accumulate skill prompt — preserves pre-matched skill context from constructor
        self._skill_prompt_addition += result.get("prompt_addition", "")

        step_result = StepResult(
            step_id=step_id,
            action=ActionType.SKILL_CALL,
            name=skill_name,
            success=result.get("found", False),
            result=f"Skill applied: {skill_name}" if result.get("found") else f"Skill not found: {skill_name}",
        )
        state.task_graph.mark_completed(step_id, step_result)

        state.skill_results[skill_name] = {"applied": result.get("found", False)}
        state.add_observation({
            "type": "skill_applied",
            "skill": skill_name,
            "found": result.get("found", False),
            "note": (
                f"Skill '{skill_name}' injected domain knowledge into your context. "
                "This is context only — NO data has been fetched yet. "
                "You MUST now call tools to gather actual data."
            ),
        })

        await self._emit_event("runtime_skill_applied", {
            "step_id": step_id,
            "skill": skill_name,
            "found": result.get("found", False),
        })

        logger.info("Skill '%s' applied (found=%s)", skill_name, result.get("found"))

    async def run(self, state: RuntimeState) -> RuntimeState:
        """
        Run the full loop until completion.

        Returns the final RuntimeState.
        """
        logger.info("Starting loop execution for: %s", state.user_query[:100])

        # Resolve DB updater once before the loop — avoids repeated module lookup every iteration
        try:
            from a2a.database import update_runtime_steps as _update_runtime_steps
        except ImportError:
            _update_runtime_steps = None

        while not state.done:
            should_continue = await self.step(state)

            # Persist context snapshot after each iteration (non-blocking)
            if state.agent_context and self._context_manager:
                try:
                    await self._context_manager.save(state.agent_context)
                except Exception as exc:
                    logger.debug("Context snapshot save skipped: %s", exc)

            # Persist accumulated steps after each iteration (non-blocking)
            if state.runtime_id and _update_runtime_steps:
                try:
                    current_steps = [
                        {
                            "step_id": s.step_id,
                            "action": s.action.value,
                            "name": s.name,
                            "goal": s.goal,
                            "status": s.status.value,
                        }
                        for s in state.task_graph.steps
                    ]
                    await _update_runtime_steps(state.runtime_id, current_steps)
                except Exception as exc:
                    logger.debug("Runtime steps update skipped: %s", exc)

            if not should_continue:
                break

        logger.info(
            "Loop completed: %d iterations, %d steps, done=%s",
            state.iteration,
            len(state.task_graph.steps),
            state.done,
        )
        return state
