"""
Tool Manager — Multi-MCP Integration.

Fetches tools from all configured MCP servers via the MCPRegistry
and executes tool calls routed to the correct server.

MCP servers are loaded from config (a2a/mcp_servers/config/mcp_servers.json)
at runtime — no hardcoded URLs or keys.

This is the single tool provider for the runtime.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from a2a.orchestrator.config import TOOL_RESULT_MAX_CHARS

logger = logging.getLogger("runtime.tool_manager")


def _truncate_result(raw: str, max_chars: int = TOOL_RESULT_MAX_CHARS) -> str:
    """Truncate oversized tool results with a clear marker."""
    if len(raw) <= max_chars:
        return raw
    return (
        f"RESULT_TRUNCATED: The tool returned ~{len(raw):,} characters. "
        f"Only the first {max_chars:,} characters are shown.\n\n"
        f"{raw[:max_chars]}\n\n... [TRUNCATED]"
    )


class ToolManager:
    """
    Manages tool discovery and execution via MCP Registry.

    Connects to all enabled MCP servers defined in config,
    aggregates their tools, and routes calls to the correct server.
    """

    def __init__(self, registry: Optional["MCPRegistry"] = None) -> None:
        # Lazy import to avoid circular imports at module level
        from a2a.orchestrator.runtime.mcp_registry import MCPRegistry

        if registry is not None:
            self._registry: MCPRegistry = registry
        else:
            # Auto-load from config when no registry is provided
            from a2a.orchestrator.runtime.mcp_loader import load_mcps_from_config

            self._registry = load_mcps_from_config()

        self._tool_schemas: Optional[List[Dict[str, Any]]] = None

    async def fetch_tools(self) -> List[Dict[str, Any]]:
        """
        Fetch all available tools from all configured MCP servers.

        Returns OpenAI-compatible function schemas.
        Caches results for the lifetime of this manager.
        """
        if self._tool_schemas is not None:
            return self._tool_schemas

        try:
            raw_tools = await self._registry.fetch_all_tools()

            logger.info(
                "Fetched %d tools from %d MCP server(s)",
                len(raw_tools),
                self._registry.client_count,
            )

            self._tool_schemas = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": (
                            t.inputSchema
                            if isinstance(t.inputSchema, dict)
                            else {"type": "object", "properties": {}}
                        ),
                    },
                }
                for t in raw_tools
            ]
            return self._tool_schemas

        except Exception as exc:
            logger.warning("Could not fetch MCP tools: %s", exc)
            self._tool_schemas = []
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a single tool, routed to the correct MCP server.

        Returns the text result with truncation applied.
        """
        logger.info("Calling MCP tool: %s with args: %s", tool_name, str(arguments)[:200])
        raw = await self._registry.call_tool(tool_name, arguments)
        return _truncate_result(raw)

    def get_tool_names(self) -> List[str]:
        """Return list of available tool names (from cache)."""
        if self._tool_schemas is None:
            return []
        return [
            t["function"]["name"]
            for t in self._tool_schemas
        ]

    def get_tool_descriptions(self) -> str:
        """Return a formatted string of tool names, descriptions, and parameters for prompts."""
        if not self._tool_schemas:
            return "No tools available."
        lines = []
        for t in self._tool_schemas:
            fn = t["function"]
            params = fn.get("parameters", {})
            props = params.get("properties", {})
            required = set(params.get("required", []))
            # Separate required and optional params
            req_parts = []
            opt_parts = []
            for pname, pschema in props.items():
                ptype = pschema.get("type", "string")
                desc = pschema.get("description", "")
                constraint = ""
                if "maximum" in pschema:
                    constraint = f" max={pschema['maximum']}"
                if "enum" in pschema:
                    constraint = f" one of {pschema['enum']}"
                entry = f"{pname}: {ptype}{constraint}"
                if desc:
                    entry += f" — {desc[:80]}"
                if pname in required:
                    req_parts.append(entry)
                else:
                    opt_parts.append(entry)
            req_str = ", ".join(req_parts) if req_parts else "none"
            opt_str = ", ".join(f"[{p}]" for p in opt_parts) if opt_parts else ""
            desc_line = f"- **{fn['name']}**({req_str}): {fn['description'][:200]}"
            if opt_str:
                desc_line += f"\n    Optional: {opt_str}"
            lines.append(desc_line)
        return "\n".join(lines)

    def clear_cache(self) -> None:
        """Clear the tool cache to force re-fetch."""
        self._tool_schemas = None
        self._registry.clear_cache()
