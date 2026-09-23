from __future__ import annotations

import socket
import tempfile
import unittest
from pathlib import Path

from mcp_generator.lifecycle import LifecycleManager
from mcp_generator.registry import ServerRegistry, write_manifest


class LifecycleManagerTests(unittest.TestCase):
    def test_start_and_stop_owned_server(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            server_dir = root / "test-mcp-12345678"
            server_dir.mkdir()
            port = _available_port()
            (server_dir / "server.py").write_text(
                f'''import socket

listener = socket.socket()
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("127.0.0.1", {port}))
listener.listen()
print("ready", flush=True)
while True:
    connection, _ = listener.accept()
    connection.close()
''',
                encoding="utf-8",
            )
            write_manifest(server_dir, _descriptor(server_dir, port))
            manager = LifecycleManager(ServerRegistry(root), startup_timeout=3)

            running = manager.start("test-mcp-12345678")
            self.assertEqual(running["runtime"]["status"], "running")
            self.assertIsInstance(running["runtime"]["pid"], int)

            stopped = manager.stop("test-mcp-12345678")
            self.assertEqual(stopped["runtime"]["status"], "stopped")

    def test_open_unowned_port_is_reported_as_external(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            server_dir = root / "external-mcp-12345678"
            server_dir.mkdir()
            (server_dir / "server.py").write_text("# generated\n", encoding="utf-8")
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                listener.listen()
                port = listener.getsockname()[1]
                write_manifest(server_dir, _descriptor(server_dir, port, "external-mcp-12345678"))

                record = LifecycleManager(ServerRegistry(root)).get_server(
                    "external-mcp-12345678"
                )

            self.assertEqual(record["runtime"]["status"], "external")


def _available_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _descriptor(server_dir: Path, port: int, server_id: str = "test-mcp-12345678") -> dict:
    return {
        "server": {
            "id": server_id,
            "name": "test-mcp",
            "title": "Test MCP",
            "description": "Test server",
            "version": "1.0.0",
        },
        "connection": {
            "transport": "streamable-http",
            "url": f"http://127.0.0.1:{port}/mcp",
        },
        "capabilities": {"tools": True, "tool_count": 1},
        "status": "generated",
        "generation": {
            "output_directory": str(server_dir),
            "openapi_source": None,
            "api_base_url": "https://api.example.com",
        },
    }


if __name__ == "__main__":
    unittest.main()
