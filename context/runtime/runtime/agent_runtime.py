"""
Agent Runtime — Top-level controller.

The single entry point for executing a user query through the runtime.

Responsibilities:
- Discover agents from registry (with TTL cache)
- Create and configure all managers
- Create execution engine
- Run execution
- Return results

Called from the runtime_executor node.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from a2a.orchestrator.runtime.execution_engine import ExecutionEngine
from a2a.orchestrator.runtime.planner import Planner
from a2a.orchestrator.runtime.tool_manager import ToolManager
from a2a.orchestrator.runtime.agent_manager import AgentManager
from a2a.orchestrator.runtime.skill_manager import SkillManager
from a2a.orchestrator.runtime.memory_store import MemoryStore
from a2a.orchestrator.runtime.state import RuntimeState
from a2a.orchestrator.context_manager import ContextManager
from a2a.orchestrator.config import REGISTRY_URL, AGENT_CACHE_TTL

logger = logging.getLogger("runtime.agent_runtime")


class AgentRuntime:
    """
    Top-level Agent Runtime controller.

    Creates all components, discovers agents, builds the execution engine,
    and runs the query through the loop execution pipeline.

    Usage::

        runtime = AgentRuntime()
        result = await runtime.run(
            user_query="Show all pods in payments namespace",
        )
    """

    def __init__(
        self,
        registry_url: str = REGISTRY_URL,
        event_callback: Optional[Callable] = None,
    ) -> None:
        self._registry_url = registry_url
        self._event_callback = event_callback

        # Shared components (reused across calls)
        self._planner = Planner()
        self._tool_manager = ToolManager()
        self._skill_manager = SkillManager()

        # Agent cache with TTL
        self._cached_agents: List[Dict[str, Any]] = []
        self._agents_cached_at: float = 0.0

    def _build_compress_fn(self) -> Callable:
        """Build a compress function using the text_explorer in-process.

        Returns an async callable: (text, goal, mode) -> compressed_text
        """
        async def _compress_fn(text: str, goal: str, mode: str = "auto") -> str:
            from a2a.agents.text_explorer.storage import DataStore
            from a2a.agents.text_explorer.tools import TextExplorerTools
            from a2a.agents.text_explorer.processor import TextProcessor

            store = DataStore()
            tools = TextExplorerTools(store)
            processor = TextProcessor(store, tools)

            data_ref = await store.store(
                content=text,
                data_type="context_compression",
                source="context_manager",
            )

            result = await processor.process(
                data_ref=data_ref,
                user_query=goal,
                goal=f"Compress context while preserving key information relevant to: {goal}",
                mode=mode if mode != "auto" else "summarize",
            )

            content = result.get("content", "")
            if not content:
                # Fallback: return first 2000 chars
                return text[:2000]
            return content

        return _compress_fn

    async def run(
        self,
        user_query: str,
        session_history: Optional[List[Dict[str, Any]]] = None,
        matched_skill: Optional[str] = None,
        knowledge_context: Optional[Dict[str, Any]] = None,
        conversation_id: str = "",
        user_id: int = 0,
        user_message_id: Optional[str] = None,
        intent: Optional[str] = None,
        intent_domain: Optional[str] = None,
        complexity: Optional[str] = None,
        page_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a user query through the full runtime pipeline.

        Agent discovery uses a TTL cache to avoid per-request registry calls.
        """
        logger.info("AgentRuntime.run() starting for: %s", user_query)

        # Discover agents with TTL cache
        agent_manager = AgentManager(registry_url=self._registry_url)
        now = time.monotonic()
        if self._cached_agents and (now - self._agents_cached_at) < AGENT_CACHE_TTL:
            agent_manager.set_agents(self._cached_agents)
            logger.info("Using cached agents (%d agents, %.1fs old)",
                        len(self._cached_agents), now - self._agents_cached_at)
        else:
            try:
                await agent_manager.discover_agents()
                self._cached_agents = agent_manager.available_agents
                self._agents_cached_at = now
            except Exception as exc:
                logger.warning("Agent discovery failed: %s — using cache", exc)
                if self._cached_agents:
                    agent_manager.set_agents(self._cached_agents)
                # If no cache, agent_manager has empty list (graceful degradation)

        # Create per-request components
        memory = MemoryStore()
        context_manager = ContextManager(
            compress_fn=self._build_compress_fn(),
        )

        # Build execution engine
        engine = ExecutionEngine(
            tool_manager=self._tool_manager,
            agent_manager=agent_manager,
            skill_manager=self._skill_manager,
            memory=memory,
            planner=self._planner,
            context_manager=context_manager,
            event_callback=self._event_callback,
        )

        # Execute
        state = await engine.execute(
            user_query=user_query,
            session_history=session_history,
            matched_skill=matched_skill,
            knowledge_context=knowledge_context,
            conversation_id=conversation_id,
            user_id=user_id,
            user_message_id=user_message_id,
            intent=intent,
            intent_domain=intent_domain,
            complexity=complexity,
            page_metadata=page_metadata,
        )

        # Build output (includes final_response + classification metadata).
        output = state.to_output()

        # Backward-compat: keep planner_context populated with the final
        # answer text for any downstream code or tests that still read it.
        if state.final_answer and not output.get("planner_context"):
            output["planner_context"] = state.final_answer

        logger.info(
            "AgentRuntime.run() completed: %d steps, %d results, final_response=%s chars",
            len(output.get("execution_plan", [])),
            len(output.get("agent_results", {})),
            len(output.get("final_response", "") or ""),
        )

        return output
