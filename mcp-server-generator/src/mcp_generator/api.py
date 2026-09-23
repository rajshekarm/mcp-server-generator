from __future__ import annotations

import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyHttpUrl, BaseModel, Field

from .descriptor import build_server_descriptor
from .generator import DEFAULT_MCP_URL, GeneratorError, generate_server
from .lifecycle import LifecycleError, LifecycleManager
from .registry import RegistryError, ServerNotFoundError, ServerRegistry, write_manifest


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
    mcp_url: AnyHttpUrl = Field(
        default=AnyHttpUrl(DEFAULT_MCP_URL),
        description=(
            "MCP endpoint URL returned to clients and used for the generated "
            "server's default host, port, and path"
        ),
    )


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


@asynccontextmanager
async def lifespan(application: FastAPI):
    registry = ServerRegistry(_output_root())
    application.state.lifecycle = LifecycleManager(registry)
    try:
        yield
    finally:
        application.state.lifecycle.stop_all()


app = FastAPI(
    title="MCP Server Generator API",
    description="Generate a FastMCP server from an OpenAPI REST API.",
    version="0.1.0",
    lifespan=lifespan,
)

dashboard_origins = [
    origin.strip()
    for origin in os.getenv(
        "MCP_DASHBOARD_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=dashboard_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _output_root() -> Path:
    configured_root = os.getenv("MCP_GENERATOR_OUTPUT_ROOT")
    if configured_root:
        return Path(configured_root).resolve()
    return Path(__file__).resolve().parents[2] / "generated"


def _server_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "mcp-server"
    return f"{slug}-{uuid4().hex[:8]}"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _lifecycle(request: Request) -> LifecycleManager:
    return request.app.state.lifecycle


def _not_found(exc: ServerNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@app.get("/mcp-servers")
def list_mcp_servers(request: Request) -> list[dict[str, Any]]:
    return _lifecycle(request).list_servers()


@app.get("/mcp-servers/{server_id}")
def get_mcp_server(server_id: str, request: Request) -> dict[str, Any]:
    try:
        return _lifecycle(request).get_server(server_id)
    except ServerNotFoundError as exc:
        raise _not_found(exc) from exc


@app.post("/mcp-servers/{server_id}/start")
def start_mcp_server(server_id: str, request: Request) -> dict[str, Any]:
    try:
        return _lifecycle(request).start(server_id)
    except ServerNotFoundError as exc:
        raise _not_found(exc) from exc
    except LifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.post("/mcp-servers/{server_id}/stop")
def stop_mcp_server(server_id: str, request: Request) -> dict[str, Any]:
    try:
        return _lifecycle(request).stop(server_id)
    except ServerNotFoundError as exc:
        raise _not_found(exc) from exc
    except LifecycleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.get("/mcp-servers/{server_id}/logs")
def get_mcp_server_logs(server_id: str, request: Request) -> dict[str, Any]:
    try:
        return _lifecycle(request).logs(server_id)
    except ServerNotFoundError as exc:
        raise _not_found(exc) from exc


@app.post(
    "/mcp-servers",
    response_model=GeneratedServerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mcp_server(request: GenerateServerRequest) -> dict:
    server_id = _server_id(request.name)
    output_dir = _output_root() / server_id

    registry = ServerRegistry(_output_root())
    try:
        registry.assert_port_available(str(request.mcp_url))
        result = generate_server(
            customer_url=str(request.api_url),
            output_dir=output_dir,
            server_name=request.name,
            mcp_url=str(request.mcp_url),
        )
    except (GeneratorError, RegistryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    descriptor = build_server_descriptor(
        result,
        server_id=server_id,
        title=request.title or request.name,
        description=request.description,
        version=request.version,
    )
    write_manifest(output_dir, descriptor)
    return descriptor


def run() -> None:
    uvicorn.run(
        "mcp_generator.api:app",
        host=os.getenv("MCP_GENERATOR_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_GENERATOR_PORT", "9000")),
    )
