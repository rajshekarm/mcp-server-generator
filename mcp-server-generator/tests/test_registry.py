from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mcp_generator.registry import (
    RegistryError,
    ServerNotFoundError,
    ServerRegistry,
    write_manifest,
)


class ServerRegistryTests(unittest.TestCase):
    def test_manifest_server_is_listed_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            server_dir = root / "weather-mcp-12345678"
            server_dir.mkdir()
            (server_dir / "server.py").write_text("# generated\n", encoding="utf-8")
            descriptor = _descriptor(server_dir)
            write_manifest(server_dir, descriptor)

            registry = ServerRegistry(root)

            self.assertEqual(registry.list()[0]["server"]["id"], "weather-mcp-12345678")
            self.assertEqual(
                registry.get("weather-mcp-12345678")["connection"]["url"],
                "http://127.0.0.1:8123/mcp",
            )

    def test_legacy_generated_server_gets_a_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            server_dir = root / "legacy-mcp-12345678"
            server_dir.mkdir()
            (server_dir / "server.py").write_text(
                '''DEFAULT_API_BASE_URL = "https://api.example.com"
mcp = FastMCP.from_openapi(openapi_spec={}, client=None, name="legacy-mcp")
mcp.run(
    transport="http",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8124")),
    path=os.getenv("MCP_PATH", "/mcp"),
)
''',
                encoding="utf-8",
            )
            (server_dir / "openapi.json").write_text(
                json.dumps(
                    {
                        "openapi": "3.1.1",
                        "info": {"title": "Legacy API", "version": "2.0"},
                        "paths": {"/items": {"get": {}}},
                    }
                ),
                encoding="utf-8",
            )

            record = ServerRegistry(root).get("legacy-mcp-12345678")

            self.assertEqual(record["server"]["name"], "legacy-mcp")
            self.assertEqual(record["capabilities"]["tool_count"], 1)
            self.assertEqual(record["connection"]["url"], "http://127.0.0.1:8124/mcp")
            self.assertTrue((server_dir / "server.json").is_file())

    def test_duplicate_port_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            server_dir = root / "weather-mcp-12345678"
            server_dir.mkdir()
            (server_dir / "server.py").write_text("# generated\n", encoding="utf-8")
            write_manifest(server_dir, _descriptor(server_dir))

            with self.assertRaisesRegex(RegistryError, "already assigned"):
                ServerRegistry(root).assert_port_available(
                    "http://127.0.0.1:8123/another-path"
                )

    def test_unknown_or_unsafe_id_is_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry = ServerRegistry(Path(temporary_directory))
            with self.assertRaises(ServerNotFoundError):
                registry.get("../outside")


def _descriptor(server_dir: Path) -> dict:
    return {
        "server": {
            "id": "weather-mcp-12345678",
            "name": "weather-mcp",
            "title": "Weather MCP",
            "description": "Weather tools",
            "version": "1.0.0",
        },
        "connection": {
            "transport": "streamable-http",
            "url": "http://127.0.0.1:8123/mcp",
        },
        "capabilities": {"tools": True, "tool_count": 4},
        "status": "generated",
        "generation": {
            "output_directory": str(server_dir),
            "openapi_source": "https://api.example.com/openapi.json",
            "api_base_url": "https://api.example.com",
        },
    }


if __name__ == "__main__":
    unittest.main()
