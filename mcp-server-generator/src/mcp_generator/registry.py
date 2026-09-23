from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


MANIFEST_NAME = "server.json"
SERVER_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
SERVER_NAME_PATTERN = re.compile(r"\bname\s*=\s*(['\"])(.*?)\1")
BASE_URL_PATTERN = re.compile(r"^DEFAULT_API_BASE_URL\s*=\s*(['\"])(.*?)\1", re.MULTILINE)
HOST_PATTERN = re.compile(
    r"host\s*=\s*os\.getenv\(\s*['\"]MCP_HOST['\"]\s*,\s*['\"]([^'\"]+)['\"]"
)
PORT_PATTERN = re.compile(
    r"port\s*=\s*int\(os\.getenv\(\s*['\"]MCP_PORT['\"]\s*,\s*['\"](\d+)['\"]"
)
PATH_PATTERN = re.compile(
    r"path\s*=\s*os\.getenv\(\s*['\"]MCP_PATH['\"]\s*,\s*['\"]([^'\"]+)['\"]"
)
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


class RegistryError(RuntimeError):
    """Raised when generated server metadata is missing or invalid."""


class ServerNotFoundError(RegistryError):
    """Raised when a generated server ID does not exist."""


def write_manifest(output_dir: Path, descriptor: dict[str, Any]) -> Path:
    """Persist a generated server descriptor next to its generated files."""
    manifest = output_dir / MANIFEST_NAME
    temporary = output_dir / f"{MANIFEST_NAME}.tmp"
    temporary.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    temporary.replace(manifest)
    return manifest


class ServerRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def list(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []

        records: list[dict[str, Any]] = []
        for directory in sorted(self.root.iterdir()):
            if not directory.is_dir() or not (directory / "server.py").is_file():
                continue
            try:
                records.append(self._load_directory(directory))
            except (OSError, ValueError, json.JSONDecodeError, RegistryError):
                # One damaged generated project must not hide every healthy one.
                continue
        return records

    def get(self, server_id: str) -> dict[str, Any]:
        directory = self._safe_directory(server_id)
        if not directory.is_dir() or not (directory / "server.py").is_file():
            raise ServerNotFoundError(f"Generated MCP server not found: {server_id}")
        return self._load_directory(directory)

    def assert_port_available(self, mcp_url: str, excluding_id: str | None = None) -> None:
        target_port = _url_port(mcp_url)
        for record in self.list():
            server_id = record["server"]["id"]
            if server_id == excluding_id:
                continue
            if _url_port(record["connection"]["url"]) == target_port:
                raise RegistryError(
                    f"MCP port {target_port} is already assigned to {server_id}"
                )

    def _safe_directory(self, server_id: str) -> Path:
        if not SERVER_ID_PATTERN.fullmatch(server_id):
            raise ServerNotFoundError(f"Invalid generated server ID: {server_id}")
        directory = (self.root / server_id).resolve()
        if directory.parent != self.root:
            raise ServerNotFoundError(f"Invalid generated server ID: {server_id}")
        return directory

    def _load_directory(self, directory: Path) -> dict[str, Any]:
        if directory.resolve().parent != self.root:
            raise RegistryError("Generated server is outside the registry root")

        manifest = directory / MANIFEST_NAME
        if manifest.is_file():
            record = json.loads(manifest.read_text(encoding="utf-8"))
        else:
            record = self._legacy_record(directory)

        expected_id = directory.name
        if record.get("server", {}).get("id") != expected_id:
            raise RegistryError(f"Manifest ID does not match directory: {expected_id}")

        record.setdefault("generation", {})["output_directory"] = str(directory)
        return record

    def _legacy_record(self, directory: Path) -> dict[str, Any]:
        source = (directory / "server.py").read_text(encoding="utf-8")
        spec_path = directory / "openapi.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.is_file() else {}

        host = _first_group(HOST_PATTERN, source, "127.0.0.1")
        port = int(_first_group(PORT_PATTERN, source, "8001"))
        path = _first_group(PATH_PATTERN, source, "/mcp")
        name = _first_group(SERVER_NAME_PATTERN, source, directory.name, group=2)
        api_base_url = _first_group(BASE_URL_PATTERN, source, "", group=2)
        info = spec.get("info") if isinstance(spec.get("info"), dict) else {}

        descriptor = {
            "server": {
                "id": directory.name,
                "name": name,
                "title": info.get("title") or name,
                "description": info.get("description") or "Generated MCP server",
                "version": str(info.get("version") or "1.0.0"),
            },
            "connection": {
                "transport": "streamable-http",
                "url": f"http://{host}:{port}{path}",
            },
            "capabilities": {
                "tools": True,
                "tool_count": _operation_count(spec),
            },
            "status": "generated",
            "generation": {
                "output_directory": str(directory),
                "openapi_source": None,
                "api_base_url": api_base_url,
            },
        }
        # Persist the migration so future reads retain a stable descriptor.
        write_manifest(directory, descriptor)
        return descriptor


def _first_group(
    pattern: re.Pattern[str], source: str, default: str, *, group: int = 1
) -> str:
    match = pattern.search(source)
    return match.group(group) if match else default


def _operation_count(spec: dict[str, Any]) -> int:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return 0
    return sum(
        1
        for path_item in paths.values()
        if isinstance(path_item, dict)
        for method in path_item
        if method.lower() in HTTP_METHODS
    )


def _url_port(url: str) -> int:
    parsed = urlparse(url)
    if parsed.port is not None:
        return parsed.port
    return 443 if parsed.scheme == "https" else 80
