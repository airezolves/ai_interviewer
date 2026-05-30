"""
Memory Store.

Lightweight metadata index for tracking tool/agent execution within
a single runtime. Stores ONLY summaries and status — the full data
lives in ContextManager (token-budgeted).

Provides a fallback context summary when the primary ContextManager
is not available (e.g., initialization failure).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("runtime.memory")

# Max entries before oldest are evicted
_MAX_TOOL_RESULTS = 30
_MAX_AGENT_RESULTS = 15
_MAX_OBSERVATIONS = 20
# Max chars for result summaries (not raw data)
_SUMMARY_CHARS = 300


class MemoryStore:
    """
    Lightweight metadata store for a single runtime execution.

    Stores ONLY summaries and metadata — not raw results.
    Full data is owned by ContextManager.

    Stores:
    - Messages (user/assistant/system LLM messages)
    - Tool result summaries keyed by invocation
    - Agent result summaries keyed by agent name
    - Observations from each loop iteration
    - Arbitrary key-value metadata
    """

    def __init__(self) -> None:
        self._messages: List[Dict[str, Any]] = []
        self._tool_results: List[Dict[str, Any]] = []
        self._agent_results: List[Dict[str, Any]] = []
        self._observations: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}

    # -- Messages ----------------------------------------------------------

    def add_message(self, role: str, content: str, **extra: Any) -> None:
        """Add a message to the conversation history."""
        msg = {"role": role, "content": content, **extra}
        self._messages.append(msg)

    @property
    def messages(self) -> List[Dict[str, Any]]:
        return list(self._messages)

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Return messages formatted for LLM API calls."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self._messages
            if m.get("content")
        ]

    # -- Tool results ------------------------------------------------------

    def add_tool_result(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        success: bool,
        step_id: str = "",
    ) -> None:
        # Store only a summary, not the raw result
        result_str = str(result) if result else ""
        summary = result_str[:_SUMMARY_CHARS] if len(result_str) > _SUMMARY_CHARS else result_str
        self._tool_results.append({
            "tool": tool_name,
            "args_keys": list(args.keys()) if isinstance(args, dict) else [],
            "summary": summary,
            "success": success,
            "step_id": step_id,
            "result_len": len(result_str),
        })
        # Evict oldest if over limit
        if len(self._tool_results) > _MAX_TOOL_RESULTS:
            self._tool_results = self._tool_results[-_MAX_TOOL_RESULTS:]

    @property
    def tool_results(self) -> List[Dict[str, Any]]:
        return list(self._tool_results)

    def get_last_tool_result(self) -> Optional[Dict[str, Any]]:
        return self._tool_results[-1] if self._tool_results else None

    # -- Agent results -----------------------------------------------------

    def add_agent_result(
        self,
        agent_name: str,
        goal: str,
        result: Any,
        success: bool,
        step_id: str = "",
    ) -> None:
        result_str = str(result) if result else ""
        summary = result_str[:_SUMMARY_CHARS] if len(result_str) > _SUMMARY_CHARS else result_str
        self._agent_results.append({
            "agent": agent_name,
            "goal": goal[:200],
            "summary": summary,
            "success": success,
            "step_id": step_id,
            "result_len": len(result_str),
        })
        if len(self._agent_results) > _MAX_AGENT_RESULTS:
            self._agent_results = self._agent_results[-_MAX_AGENT_RESULTS:]

    @property
    def agent_results(self) -> List[Dict[str, Any]]:
        return list(self._agent_results)

    # -- Observations ------------------------------------------------------

    def add_observation(self, observation: Dict[str, Any]) -> None:
        self._observations.append(observation)
        if len(self._observations) > _MAX_OBSERVATIONS:
            self._observations = self._observations[-_MAX_OBSERVATIONS:]

    @property
    def observations(self) -> List[Dict[str, Any]]:
        return list(self._observations)

    # -- Metadata ----------------------------------------------------------

    def set(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    # -- Context for planner -----------------------------------------------

    def get_context_summary(self, max_results: int = 10) -> str:
        """Build a text summary of memory for the planner prompt.

        This is a FALLBACK — primary context comes from ContextManager.
        Only used when ContextManager is not initialized.
        """
        parts: List[str] = []

        if self._tool_results:
            parts.append("## Previous Tool Results")
            for tr in self._tool_results[-max_results:]:
                status = "OK" if tr["success"] else "FAILED"
                summary = tr.get("summary", "")
                if tr["success"] and not summary.strip():
                    status = "EMPTY"
                parts.append(
                    f"- [{status}] {tr['tool']} ({tr.get('result_len', 0)} chars): {summary[:200]}"
                )

        if self._agent_results:
            parts.append("\n## Previous Agent Results")
            for ar in self._agent_results[-max_results:]:
                status = "OK" if ar["success"] else "FAILED"
                parts.append(
                    f"- [{status}] {ar['agent']} (goal: {ar.get('goal', '')[:150]}): {ar.get('summary', '')[:200]}"
                )

        if self._observations:
            parts.append("\n## Observations")
            for obs in self._observations[-5:]:
                parts.append(f"- {obs}")

        return "\n".join(parts) if parts else "No previous results."

    def clear(self) -> None:
        """Reset all memory."""
        self._messages.clear()
        self._tool_results.clear()
        self._agent_results.clear()
        self._observations.clear()
        self._metadata.clear()
