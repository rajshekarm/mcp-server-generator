"""Generate a FastMCP server from a REST API's OpenAPI document."""

from .generator import (
    DEFAULT_MCP_URL,
    GenerationResult,
    GeneratorError,
    generate_server,
)

__all__ = [
    "DEFAULT_MCP_URL",
    "GenerationResult",
    "GeneratorError",
    "generate_server",
]
