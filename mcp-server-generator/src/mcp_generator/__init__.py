"""Generate a FastMCP server from a REST API's OpenAPI document."""

from .generator import (
    DEFAULT_MCP_URL,
    GenerationResult,
    GeneratorError,
    generate_server,
)
from .descriptor import build_server_descriptor

__all__ = [
    "DEFAULT_MCP_URL",
    "GenerationResult",
    "GeneratorError",
    "build_server_descriptor",
    "generate_server",
]
