"""
MCP Loader — Load MCP servers from JSON config.

Reads the MCP servers config file, resolves environment variable
placeholders, validates entries, and builds an MCPRegistry with
all enabled MCPClient instances.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

from a2a.orchestrator.clients.mcp_client import MCPClient
from a2a.orchestrator.runtime.mcp_registry import MCPRegistry

logger = logging.getLogger("runtime.mcp_loader")

# Default config path (relative to this file → orchestrator/runtime/ → up to mcp_servers/config/)
_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "mcp_servers",
    "config",
    "mcp_servers.json",
)

# Pattern for ${ENV_VAR} or ${ENV_VAR:-default} placeholders
_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(value: str) -> str:
    """
    Resolve ${ENV_VAR} placeholders in a string.

    Supports:
    - ${VAR} — replaced with os.environ["VAR"], empty string if not set
    - ${VAR:-default} — replaced with os.environ.get("VAR", "default")
    """

    def _replace(match: re.Match) -> str:
        expr = match.group(1)
        if ":-" in expr:
            var_name, default = expr.split(":-", 1)
            return os.environ.get(var_name.strip(), default)
        return os.environ.get(expr.strip(), "")

    return _ENV_PATTERN.sub(_replace, value)


def _resolve_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively resolve env vars in all string values of a dict."""
    resolved = {}
    for key, value in d.items():
        if isinstance(value, str):
            resolved[key] = _resolve_env_vars(value)
        elif isinstance(value, dict):
            resolved[key] = _resolve_dict(value)
        elif isinstance(value, list):
            resolved[key] = [
                _resolve_env_vars(v) if isinstance(v, str) else v for v in value
            ]
        else:
            resolved[key] = value
    return resolved


def _validate_mcp_entry(entry: Dict[str, Any], index: int) -> bool:
    """Validate a single MCP config entry."""
    name = entry.get("name")
    url = entry.get("url")
    transport = entry.get("transport")

    if not name:
        logger.warning("MCP entry %d missing 'name' — skipping", index)
        return False
    if not url:
        logger.warning("MCP entry %d ('%s') missing 'url' — skipping", index, name)
        return False
    if not transport:
        logger.warning("MCP entry %d ('%s') missing 'transport' — skipping", index, name)
        return False
    return True


def load_mcps_from_config(
    config_path: Optional[str] = None,
) -> MCPRegistry:
    """
    Load MCP servers from a JSON config file and return a populated MCPRegistry.

    Args:
        config_path: Path to the JSON config file.
                     Defaults to a2a/mcp_servers/config/mcp_servers.json.

    Returns:
        MCPRegistry with all enabled MCPClient instances registered.
    """
    config_path = config_path or os.environ.get("MCP_CONFIG_PATH", _DEFAULT_CONFIG_PATH)

    if not os.path.exists(config_path):
        logger.warning(
            "MCP config file not found at %s — returning empty registry", config_path
        )
        return MCPRegistry()

    try:
        with open(config_path, "r") as f:
            raw_config = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read MCP config from %s: %s", config_path, exc)
        return MCPRegistry()

    mcps = raw_config.get("mcps", [])
    if not isinstance(mcps, list):
        logger.error("MCP config 'mcps' field must be a list — got %s", type(mcps).__name__)
        return MCPRegistry()

    registry = MCPRegistry()
    loaded = 0

    for i, raw_entry in enumerate(mcps):
        # Resolve env vars in all string values
        entry = _resolve_dict(raw_entry)

        # Validate
        if not _validate_mcp_entry(entry, i):
            continue

        # Check enabled flag (default: True)
        if not entry.get("enabled", True):
            logger.info("MCP '%s' is disabled — skipping", entry["name"])
            continue

        # Build client
        client = MCPClient(
            name=entry["name"],
            url=entry["url"],
            transport=entry["transport"],
            headers=entry.get("headers"),
            timeout=entry.get("timeout", 30),
        )
        registry.register(client)
        loaded += 1

    logger.info(
        "Loaded %d MCP server(s) from config (%d total, %d enabled)",
        loaded,
        len(mcps),
        loaded,
    )
    return registry
