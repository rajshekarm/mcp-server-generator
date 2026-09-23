from __future__ import annotations

import unittest

from mcp_generator.generator import (
    GeneratorError,
    _mcp_runtime_defaults,
    _normalize_openapi_for_fastmcp,
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


class OpenApiCompatibilityTests(unittest.TestCase):
    def test_openapi_312_is_normalized_for_fastmcp(self) -> None:
        original = {"openapi": "3.1.2", "paths": {"/alerts": {"get": {}}}}

        normalized = _normalize_openapi_for_fastmcp(original)

        self.assertEqual(normalized["openapi"], "3.1.1")
        self.assertEqual(original["openapi"], "3.1.2")
        self.assertIs(normalized["paths"], original["paths"])

    def test_supported_openapi_version_is_unchanged(self) -> None:
        document = {"openapi": "3.1.1", "paths": {}}

        self.assertEqual(
            _normalize_openapi_for_fastmcp(document)["openapi"],
            "3.1.1",
        )


if __name__ == "__main__":
    unittest.main()
