"""
MCP Registry — Central registry for all MCP server clients.

Stores MCPClient instances, provides unified tool discovery and routing.
Maps tool names to their source MCP server for correct call dispatch.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from a2a.orchestrator.clients.mcp_client import MCPClient

logger = logging.getLogger("runtime.mcp_registry")


class MCPRegistry:
    """
    Central registry for all configured MCP servers.

    Responsibilities:
    - Store all MCPClient instances
    - Aggregate tools from all enabled MCPs
    - Route tool calls to the correct MCP server
    - Maintain tool_name → MCPClient mapping
    """

    def __init__(self) -> None:
        self._clients: Dict[str, MCPClient] = {}
        self._tool_to_client: Dict[str, MCPClient] = {}
        self._tools_fetched: bool = False

    def register(self, client: MCPClient) -> None:
        """Register an MCP client."""
        self._clients[client.name] = client
        logger.info("Registered MCP: %s (%s)", client.name, client.url)

    def get_all(self) -> List[MCPClient]:
        """Return all registered MCP clients."""
        return list(self._clients.values())

    def get_mcp(self, name: str) -> Optional[MCPClient]:
        """Return a specific MCP client by name."""
        return self._clients.get(name)

    @property
    def client_count(self) -> int:
        """Number of registered MCP clients."""
        return len(self._clients)

    async def fetch_all_tools(self) -> List:
        """
        Fetch tools from all registered MCP servers in parallel.

        Builds the tool_name → MCPClient routing map.
        Returns a flat list of all raw MCP tool objects.
        """
        if self._tools_fetched and self._tool_to_client:
            all_tools = []
            for client in self._clients.values():
                if client._tools_cache is not None:
                    all_tools.extend(client._tools_cache)
            return all_tools

        import asyncio

        all_tools = []
        self._tool_to_client.clear()

        async def _fetch_from(client: MCPClient):
            tools = await client.list_tools()
            return client, tools

        tasks = [_fetch_from(c) for c in self._clients.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Failed to fetch tools from an MCP: %s", result)
                continue
            client, tools = result
            for tool in tools:
                if tool.name in self._tool_to_client:
                    logger.warning(
                        "Duplicate tool '%s' from MCP '%s' — already registered from '%s'. Skipping.",
                        tool.name,
                        client.name,
                        self._tool_to_client[tool.name].name,
                    )
                    continue
                self._tool_to_client[tool.name] = client
                all_tools.append(tool)

        self._tools_fetched = True
        logger.info(
            "Registry aggregated %d tools from %d MCPs",
            len(all_tools),
            len(self._clients),
        )
        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Route a tool call to the correct MCP server.

        Looks up tool_name in the routing map and delegates to
        the appropriate MCPClient.

        Raises KeyError if tool is not found in any MCP.
        """
        client = self._tool_to_client.get(tool_name)
        if client is None:
            # Tools might not be fetched yet or tool doesn't exist
            if not self._tools_fetched:
                await self.fetch_all_tools()
                client = self._tool_to_client.get(tool_name)
            if client is None:
                raise KeyError(
                    f"Tool '{tool_name}' not found in any registered MCP server"
                )

        return await client.call_tool(tool_name, arguments)

    def get_tool_names(self) -> List[str]:
        """Return all available tool names."""
        return list(self._tool_to_client.keys())

    def get_client_for_tool(self, tool_name: str) -> Optional[MCPClient]:
        """Return the MCPClient that owns a given tool."""
        return self._tool_to_client.get(tool_name)

    def clear_cache(self) -> None:
        """Clear all tool caches across all MCPs."""
        self._tool_to_client.clear()
        self._tools_fetched = False
        for client in self._clients.values():
            client.clear_cache()
        logger.info("Registry cache cleared for all MCPs")
