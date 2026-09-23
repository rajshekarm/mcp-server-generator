from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx


OPENAPI_PATHS = ("openapi.json", "swagger.json", "v3/api-docs")
GENERATED_FILES = (
    "server.py",
    "server.json",
    "openapi.json",
    "requirements.txt",
    "README.md",
)
DEFAULT_MCP_URL = "http://127.0.0.1:8001/mcp"


class GeneratorError(RuntimeError):
    """Raised when an MCP server cannot be generated from the supplied URL."""


@dataclass(frozen=True)
class GenerationResult:
    output_dir: Path
    server_name: str
    openapi_url: str
    api_base_url: str
    mcp_url: str
    operation_count: int


def _validate_url(value: str, option_name: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise GeneratorError(
            f"{option_name} must be an absolute http:// or https:// URL"
        )
    try:
        parsed.port
    except ValueError as exc:
        raise GeneratorError(f"{option_name} contains an invalid port") from exc
    return normalized


def _looks_like_openapi(document: Any) -> bool:
    return (
        isinstance(document, dict)
        and isinstance(document.get("openapi"), str)
        and document["openapi"].startswith("3.")
        and isinstance(document.get("paths"), dict)
    )


def _normalize_openapi_for_fastmcp(
    document: dict[str, Any],
) -> dict[str, Any]:
    """Return a FastMCP-compatible copy of an OpenAPI document.

    FastMCP 4.0.1's parser currently accepts OpenAPI 3.1.0 and 3.1.1,
    while some APIs already publish later 3.1 patch releases such as 3.1.2.
    OpenAPI patch releases are backwards compatible, so advertise 3.1.1 to
    the parser without changing the API paths, schemas, or operations.
    """
    normalized = document.copy()
    version = normalized.get("openapi")
    if (
        isinstance(version, str)
        and re.fullmatch(r"3\.1\.\d+", version)
        and version not in {"3.1.0", "3.1.1"}
    ):
        normalized["openapi"] = "3.1.1"
    return normalized


def _candidate_urls(customer_url: str) -> list[str]:
    candidates = [customer_url]
    for path in OPENAPI_PATHS:
        candidate = f"{customer_url}/{path}"
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _discover_openapi(customer_url: str) -> tuple[str, dict[str, Any]]:
    failures: list[str] = []

    with httpx.Client(timeout=httpx.Timeout(10.0), follow_redirects=True) as client:
        for candidate in _candidate_urls(customer_url):
            try:
                response = client.get(candidate)
                response.raise_for_status()
                document = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                failures.append(f"{candidate}: {exc}")
                continue

            if _looks_like_openapi(document):
                return str(response.url), document

            failures.append(f"{candidate}: response is not an OpenAPI 3 document")

    attempted = "\n  - ".join(failures)
    raise GeneratorError(
        "No OpenAPI 3 JSON document was found. Attempted:\n  - " + attempted
    )


def _derive_api_base_url(
    customer_url: str,
    openapi_url: str,
    document: dict[str, Any],
) -> str:
    servers = document.get("servers")
    if isinstance(servers, list) and servers:
        server_url = servers[0].get("url") if isinstance(servers[0], dict) else None
        if isinstance(server_url, str) and server_url.strip():
            return urljoin(openapi_url, server_url).rstrip("/")

    parsed_openapi_url = urlparse(openapi_url)
    for suffix in ("/openapi.json", "/swagger.json", "/v3/api-docs"):
        if parsed_openapi_url.path.endswith(suffix):
            base_path = parsed_openapi_url.path[: -len(suffix)]
            return parsed_openapi_url._replace(
                path=base_path,
                params="",
                query="",
                fragment="",
            ).geturl().rstrip("/")

    return customer_url.rstrip("/")


def _operation_count(document: dict[str, Any]) -> int:
    methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
    return sum(
        1
        for path_item in document["paths"].values()
        if isinstance(path_item, dict)
        for method in path_item
        if method.lower() in methods
    )


def _mcp_runtime_defaults(mcp_url: str) -> tuple[str, int, str]:
    parsed = urlparse(mcp_url)
    if parsed.query or parsed.fragment:
        raise GeneratorError("--mcp-url cannot contain a query string or fragment")

    host = parsed.hostname
    if host is None:
        raise GeneratorError("--mcp-url must contain a host")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/mcp"
    return host, port, path


def _server_source(server_name: str, api_base_url: str, mcp_url: str) -> str:
    mcp_host, mcp_port, mcp_path = _mcp_runtime_defaults(mcp_url)
    encoded_name = json.dumps(server_name)
    encoded_base_url = json.dumps(api_base_url)
    encoded_mcp_host = json.dumps(mcp_host)
    encoded_mcp_path = json.dumps(mcp_path)
    return f'''from __future__ import annotations

import json
import os
from pathlib import Path

import httpx2
from fastmcp import FastMCP


SPEC_PATH = Path(__file__).with_name("openapi.json")
DEFAULT_API_BASE_URL = {encoded_base_url}

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
    name={encoded_name},
)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.getenv("MCP_HOST", {encoded_mcp_host}),
        port=int(os.getenv("MCP_PORT", "{mcp_port}")),
        path=os.getenv("MCP_PATH", {encoded_mcp_path}),
    )
'''


def _readme(
    server_name: str,
    api_base_url: str,
    mcp_url: str,
    operation_count: int,
) -> str:
    return f"""# {server_name}

Generated from an OpenAPI 3 REST API. FastMCP exposes each of the
{operation_count} OpenAPI operations as an MCP tool.

## Run

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python server.py
```

After the server is started, MCP clients can connect to `{mcp_url}`.

The generated default REST API base URL is `{api_base_url}`. Override it when
needed:

```powershell
$env:API_BASE_URL = "https://another-api.example.com"
python server.py
```

You can also configure `MCP_HOST`, `MCP_PORT`, and `MCP_PATH`.
"""


def generate_server(
    customer_url: str,
    output_dir: Path,
    server_name: str = "Generated REST API MCP",
    mcp_url: str = DEFAULT_MCP_URL,
    force: bool = False,
) -> GenerationResult:
    normalized_url = _validate_url(customer_url, "--url")
    normalized_mcp_url = _validate_url(mcp_url, "--mcp-url")
    _mcp_runtime_defaults(normalized_mcp_url)
    normalized_name = server_name.strip()
    if not normalized_name:
        raise GeneratorError("The server name cannot be empty")

    openapi_url, document = _discover_openapi(normalized_url)
    document = _normalize_openapi_for_fastmcp(document)
    api_base_url = _derive_api_base_url(normalized_url, openapi_url, document)
    operation_count = _operation_count(document)
    if operation_count == 0:
        raise GeneratorError("The OpenAPI document contains no REST operations")

    output_dir = output_dir.resolve()
    existing = [name for name in GENERATED_FILES if (output_dir / name).exists()]
    if existing and not force:
        raise GeneratorError(
            f"{output_dir} already contains generated files: {', '.join(existing)}. "
            "Use --force to overwrite them."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "openapi.json").write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "server.py").write_text(
        _server_source(normalized_name, api_base_url, normalized_mcp_url),
        encoding="utf-8",
    )
    (output_dir / "requirements.txt").write_text(
        "fastmcp>=4.0\nhttpx2>=2.5\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        _readme(
            normalized_name,
            api_base_url,
            normalized_mcp_url,
            operation_count,
        ),
        encoding="utf-8",
    )

    return GenerationResult(
        output_dir=output_dir,
        server_name=normalized_name,
        openapi_url=openapi_url,
        api_base_url=api_base_url,
        mcp_url=normalized_mcp_url,
        operation_count=operation_count,
    )
