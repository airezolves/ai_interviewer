"""
Execution Engine.

Controls the full execution lifecycle:
1. Initialize managers (tools, agents, skills)
2. Build initial state
3. Run the loop executor
4. Return results

The engine is created by the AgentRuntime and orchestrates all components.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from a2a.orchestrator.runtime.state import RuntimeState
from a2a.orchestrator.runtime.planner import Planner
from a2a.orchestrator.runtime.loop_executor import LoopExecutor
from a2a.orchestrator.runtime.tool_manager import ToolManager
from a2a.orchestrator.runtime.agent_manager import AgentManager
from a2a.orchestrator.runtime.skill_manager import SkillManager
from a2a.orchestrator.runtime.memory_store import MemoryStore
from a2a.orchestrator.context_manager import ContextManager
from a2a.orchestrator.config import RUNTIME_MAX_ITERATIONS, RUNTIME_MAX_BATCH_SIZE

logger = logging.getLogger("runtime.engine")


class ExecutionEngine:
    """
    Coordinates the execution of a single runtime request.

    Owns:
    - RuntimeState
    - Planner
    - LoopExecutor
    - All managers (tool, agent, skill)
    - Memory

    Does NOT own the LLM model — the Planner does.
    """

    def __init__(
        self,
        tool_manager: ToolManager,
        agent_manager: AgentManager,
        skill_manager: SkillManager,
        memory: MemoryStore,
        planner: Planner,
        context_manager: ContextManager,
        event_callback: Optional[Callable] = None,
    ) -> None:
        self._tool_manager = tool_manager
        self._agent_manager = agent_manager
        self._skill_manager = skill_manager
        self._memory = memory
        self._planner = planner
        self._context_manager = context_manager
        self._event_callback = event_callback

    async def execute(
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
    ) -> RuntimeState:
        """
        Run the full execution pipeline.

        Steps:
        1. Fetch tools from MCP Gateway
        2. Build RuntimeState
        3. Create LoopExecutor
        4. Run the loop
        5. Return final state
        """
        logger.info("Execution engine starting for: %s", user_query)

        # -- Step 1: Fetch tools from MCP Gateway --
        tools = await self._tool_manager.fetch_tools()
        if not tools:
            logger.warning(
                "No tools loaded from MCP Gateway — planner will rely on agents only"
            )
        else:
            logger.info("Loaded %d tools from MCP Gateway", len(tools))

        # -- Step 2: Build state --
        agent_list = self._agent_manager.available_agents

        state = RuntimeState(
            user_query=user_query,
            session_history=session_history,
            available_tools=tools,
            available_agents=agent_list,
            available_skills=self._skill_manager.get_skill_schemas(),
            knowledge_context=knowledge_context,
            max_iterations=RUNTIME_MAX_ITERATIONS,
        )

        # Set intent metadata for planner hints
        state.intent = intent
        state.intent_domain = intent_domain
        state.complexity = complexity

        # -- Step 3: Create runtime DB row (status='running') --
        if conversation_id:
            try:
                from a2a.database import create_runtime
                from a2a.shared.model_factory import get_model_display_name

                model_name = get_model_display_name()
                runtime_id = await create_runtime(
                    conversation_id=conversation_id,
                    user_message_id=user_message_id,
                    model=model_name,
                )
                state.runtime_id = runtime_id
                state.run_id = runtime_id  # Align run_id with DB-assigned ID
                logger.info("Runtime DB row created: %s (status=running)", runtime_id)
            except Exception as exc:
                logger.warning("Failed to create runtime DB row (non-fatal): %s", exc)

        # -- Step 4: Initialise context manager --
        agent_context = self._context_manager.init_context(
            goal=user_query,
            constraints=[],
            conversation_id=conversation_id,
            user_id=user_id,
            run_id=state.run_id,
        )

        # -- Step 5: Ingest session history into context (if provided) --
        if session_history:
            agent_context = self._context_manager.ingest_session_history(
                agent_context, session_history
            )

        # -- Step 5b: Ingest page metadata into context (if provided) --
        if page_metadata:
            logger.info(
                "Ingesting page metadata into context (%d chars, keys: %s)",
                len(str(page_metadata)),
                list(page_metadata.keys()) if isinstance(page_metadata, dict) else "raw",
            )
            agent_context = self._context_manager.ingest_page_metadata(
                agent_context, page_metadata
            )
        else:
            logger.info("No page metadata to ingest")

        # Attach context manager and context to state for downstream access
        state.context_manager = self._context_manager
        state.agent_context = agent_context

        if self._event_callback:
            try:
                await self._event_callback("runtime_start", {
                    "tools_count": len(tools),
                    "agents_count": len(agent_list),
                    "skills_count": len(self._skill_manager.list_skills()),
                    "matched_skill": matched_skill,
                    "query": user_query,
                })
            except Exception as exc:
                logger.warning("Event callback failed for runtime_start: %s", exc)

        # -- Step 6: Apply matched skill (inject domain knowledge) --
        skill_prompt_addition = ""
        if matched_skill:
            skill_result = self._skill_manager.apply_skill(matched_skill)
            if skill_result.get("found"):
                skill_prompt_addition = skill_result.get("prompt_addition", "")
                logger.info(
                    "Applied matched skill '%s' (%d chars of domain knowledge)",
                    matched_skill,
                    len(skill_prompt_addition),
                )
                if self._event_callback:
                    try:
                        await self._event_callback("runtime_skill_applied", {
                            "skill": matched_skill,
                            "found": True,
                        })
                    except Exception as exc:
                        logger.warning("Event callback failed for runtime_skill_applied: %s", exc)
            else:
                logger.warning("Matched skill '%s' not found in loaded skills", matched_skill)

        # -- Step 7: Create loop executor --
        loop_executor = LoopExecutor(
            planner=self._planner,
            tool_manager=self._tool_manager,
            agent_manager=self._agent_manager,
            skill_manager=self._skill_manager,
            memory=self._memory,
            context_manager=self._context_manager,
            event_callback=self._event_callback,
            initial_skill_prompt=skill_prompt_addition,
            max_batch_size=RUNTIME_MAX_BATCH_SIZE,
        )

        # -- Step 8: Run the loop --
        state = await loop_executor.run(state)

        if self._event_callback:
            try:
                await self._event_callback("runtime_complete", {
                    "iterations": state.iteration,
                    "steps": len(state.task_graph.steps),
                    "has_answer": state.final_answer is not None,
                })
            except Exception as exc:
                logger.warning("Event callback failed for runtime_complete: %s", exc)

        logger.info(
            "Execution engine completed: %d iterations, %d steps",
            state.iteration,
            len(state.task_graph.steps),
        )

        return state
