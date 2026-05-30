"""
Agent Manager — Sub-agent execution via A2A protocol.

Manages discovery and invocation of sub-agents through the A2A registry.
Agents are called for task execution and delegation, NOT for data loading.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from a2a.orchestrator.clients.agent_client import AgentClient
from a2a.orchestrator.clients.registry_client import RegistryClient
from a2a.orchestrator.config import REGISTRY_URL, agent_event_queue_var

logger = logging.getLogger("runtime.agent_manager")


class AgentManager:
    """
    Manages sub-agent discovery and execution via A2A protocol.

    Sub-agents are invoked via the standard A2A task execution endpoints.
    Events from agent execution are forwarded to the streaming queue.
    """

    def __init__(
        self,
        registry_url: str = REGISTRY_URL,
        available_agents: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._registry_url = registry_url
        self._agent_client = AgentClient()
        self._available_agents = available_agents or []

    async def discover_agents(self) -> List[Dict[str, Any]]:
        """Discover available agents from the registry."""
        registry = RegistryClient(registry_url=self._registry_url)
        agents = await registry.discover_agents()

        self._available_agents = [
            {
                "name": a.name,
                "description": a.description,
                "url": a.url,
                "skills": a.skills if isinstance(a.skills, list) else [],
                "tags": a.tags if isinstance(a.tags, list) else [],
            }
            for a in agents
        ]
        logger.info("Discovered %d agents from registry", len(self._available_agents))
        return self._available_agents

    @property
    def available_agents(self) -> List[Dict[str, Any]]:
        return self._available_agents

    def set_agents(self, agents: List[Dict[str, Any]]) -> None:
        """Set available agents directly (e.g., from prior discovery)."""
        self._available_agents = agents

    def resolve_agent_url(self, agent_name: str) -> Optional[str]:
        """Resolve agent name to URL."""
        name_lower = agent_name.lower()
        for agent in self._available_agents:
            if agent["name"].lower() == name_lower:
                return agent["url"]
        return None

    async def call_agent(
        self,
        agent_name: str,
        goal: str,
        user_query: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task on a sub-agent via A2A protocol.

        Uses streaming execution to forward live events.
        Returns the step result dict.
        """
        agent_url = self.resolve_agent_url(agent_name)
        if not agent_url:
            logger.warning("Agent not found: %s", agent_name)
            return {
                "agent": agent_name,
                "success": False,
                "summary": f"Agent '{agent_name}' not found in registry",
                "results": [],
            }

        step = {
            "step_id": f"agent_{agent_name}",
            "agent_name": agent_name,
            "agent_url": agent_url,
            "goal": goal,
            "depends_on": [],
        }

        logger.info("Calling agent: %s at %s", agent_name, agent_url)

        try:
            result = await self._agent_client._execute_single_step_streaming(
                step=step,
                user_query=user_query,
                context=context or {},
                conversation_id=conversation_id,
            )
            return result
        except Exception as exc:
            logger.error("Agent call failed for %s: %s", agent_name, exc)
            return {
                "step_id": step["step_id"],
                "agent": agent_name,
                "success": False,
                "summary": f"Agent execution failed: {exc}",
                "results": [],
            }

    async def call_agent_batch(
        self,
        calls: List[Dict[str, Any]],
        user_query: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute multiple agent calls with dependency awareness.

        Each call dict should have: agent_name, goal, depends_on (list of step_ids).
        Calls without dependencies run in parallel.
        """
        plan = []
        for call in calls:
            agent_url = self.resolve_agent_url(call["agent_name"])
            if not agent_url:
                logger.warning("Skipping unknown agent: %s", call["agent_name"])
                continue
            plan.append({
                "step_id": call.get("step_id", f"agent_{call['agent_name']}"),
                "agent_name": call["agent_name"],
                "agent_url": agent_url,
                "goal": call["goal"],
                "depends_on": call.get("depends_on", []),
            })

        if not plan:
            return {}

        return await self._agent_client.execute_plan_with_dependencies_streaming(
            plan=plan,
            user_query=user_query,
            conversation_id=conversation_id,
        )

    def get_agent_descriptions(self) -> str:
        """Return a formatted string of agents for prompts."""
        if not self._available_agents:
            return "No agents available."
        lines = []
        for a in self._available_agents:
            skills = ", ".join(
                s["name"] if isinstance(s, dict) else str(s)
                for s in a.get("skills", [])
            )
            lines.append(
                f"- **{a['name']}** ({a['url']}): {a['description'][:150]}"
                f"{f' | Skills: {skills}' if skills else ''}"
            )
        return "\n".join(lines)
