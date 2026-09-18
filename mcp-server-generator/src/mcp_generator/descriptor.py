from __future__ import annotations

from typing import Any

from .generator import GenerationResult


def build_server_descriptor(
    result: GenerationResult,
    *,
    server_id: str,
    title: str,
    description: str,
    version: str,
) -> dict[str, Any]:
    """Build client-neutral metadata for a generated MCP server."""

    return {
        "server": {
            "id": server_id,
            "name": result.server_name,
            "title": title,
            "description": description,
            "version": version,
        },
        "connection": {
            "transport": "streamable-http",
            "url": result.mcp_url,
        },
        "capabilities": {
            "tools": True,
            "tool_count": result.operation_count,
        },
        "status": "generated",
        "generation": {
            "output_directory": str(result.output_dir),
            "openapi_source": result.openapi_url,
            "api_base_url": result.api_base_url,
        },
    }
