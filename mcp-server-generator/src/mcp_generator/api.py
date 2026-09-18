from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import AnyHttpUrl, BaseModel, Field

from .descriptor import build_server_descriptor
from .generator import DEFAULT_MCP_URL, GeneratorError, generate_server


class GenerateServerRequest(BaseModel):
    api_url: AnyHttpUrl
    name: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str = Field(
        default="MCP tools generated from a REST API",
        min_length=1,
        max_length=1000,
    )
    version: str = Field(default="1.0.0", min_length=1, max_length=50)
    mcp_url: AnyHttpUrl = AnyHttpUrl(DEFAULT_MCP_URL)


class ServerIdentity(BaseModel):
    id: str
    name: str
    title: str
    description: str
    version: str


class ConnectionInfo(BaseModel):
    transport: Literal["streamable-http"]
    url: str


class CapabilityInfo(BaseModel):
    tools: bool
    tool_count: int


class GenerationInfo(BaseModel):
    output_directory: str
    openapi_source: str
    api_base_url: str


class GeneratedServerResponse(BaseModel):
    server: ServerIdentity
    connection: ConnectionInfo
    capabilities: CapabilityInfo
    status: Literal["generated"]
    generation: GenerationInfo


app = FastAPI(
    title="MCP Server Generator API",
    description="Generate a FastMCP server from an OpenAPI REST API.",
    version="0.1.0",
)


def _output_root() -> Path:
    configured_root = os.getenv("MCP_GENERATOR_OUTPUT_ROOT", "generated")
    return Path(configured_root).resolve()


def _server_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "mcp-server"
    return f"{slug}-{uuid4().hex[:8]}"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/mcp-servers",
    response_model=GeneratedServerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mcp_server(request: GenerateServerRequest) -> dict:
    server_id = _server_id(request.name)
    output_dir = _output_root() / server_id

    try:
        result = generate_server(
            customer_url=str(request.api_url),
            output_dir=output_dir,
            server_name=request.name,
            mcp_url=str(request.mcp_url),
        )
    except GeneratorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return build_server_descriptor(
        result,
        server_id=server_id,
        title=request.title or request.name,
        description=request.description,
        version=request.version,
    )


def run() -> None:
    uvicorn.run(
        "mcp_generator.api:app",
        host=os.getenv("MCP_GENERATOR_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_GENERATOR_PORT", "9000")),
    )
