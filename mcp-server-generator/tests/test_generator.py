from __future__ import annotations

import unittest

from mcp_generator.generator import (
    GeneratorError,
    _mcp_runtime_defaults,
    _server_source,
)


class McpRuntimeDefaultsTests(unittest.TestCase):
    def test_explicit_url_controls_generated_runtime_defaults(self) -> None:
        source = _server_source(
            "claims-mcp",
            "https://api.example.com/v1",
            "http://127.0.0.1:8123/custom-mcp",
        )

        self.assertIn('host=os.getenv("MCP_HOST", "127.0.0.1")', source)
        self.assertIn('port=int(os.getenv("MCP_PORT", "8123"))', source)
        self.assertIn('path=os.getenv("MCP_PATH", "/custom-mcp")', source)

    def test_missing_path_defaults_to_mcp(self) -> None:
        self.assertEqual(
            _mcp_runtime_defaults("http://localhost:9001"),
            ("localhost", 9001, "/mcp"),
        )

    def test_query_string_is_rejected(self) -> None:
        with self.assertRaisesRegex(GeneratorError, "query string or fragment"):
            _mcp_runtime_defaults("http://localhost:9001/mcp?token=example")


if __name__ == "__main__":
    unittest.main()
