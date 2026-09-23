from __future__ import annotations

import json
import os
from pathlib import Path

import httpx2
from fastmcp import FastMCP


SPEC_PATH = Path(__file__).with_name("openapi.json")
DEFAULT_API_BASE_URL = "https://api.weather.gov"

with SPEC_PATH.open(encoding="utf-8") as spec_file:
    openapi_spec = json.load(spec_file)

api_client = httpx2.AsyncClient(
    base_url=os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL),
    timeout=httpx2.Timeout(15.0),
    limits=httpx2.Limits(max_connections=100, max_keepalive_connections=20),
)

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=api_client,
    name="national-weather-mcp",
)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8007")),
        path=os.getenv("MCP_PATH", "/mcp"),
    )
