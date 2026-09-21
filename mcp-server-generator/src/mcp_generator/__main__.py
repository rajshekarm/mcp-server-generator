from __future__ import annotations

import argparse
from pathlib import Path

from .generator import DEFAULT_MCP_URL, GeneratorError, generate_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a ready-to-run MCP server from an OpenAPI REST API."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="REST API base URL or the URL of its OpenAPI JSON document.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Directory where the generated MCP server will be written.",
    )
    parser.add_argument(
        "--name",
        default="Generated REST API MCP",
        help="Name advertised by the generated MCP server.",
    )
    parser.add_argument(
        "--mcp-url",
        default=DEFAULT_MCP_URL,
        help=(
            "MCP endpoint returned to clients and used for the generated "
            "server's default host, port, and path "
            f"(default: {DEFAULT_MCP_URL})."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite generator-owned files if they already exist.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        result = generate_server(
            customer_url=args.url,
            output_dir=args.output,
            server_name=args.name,
            mcp_url=args.mcp_url,
            force=args.force,
        )
    except GeneratorError as exc:
        print(f"Generation failed: {exc}")
        return 1

    print(f"Generated MCP server: {result.output_dir}")
    print(f"OpenAPI source:       {result.openapi_url}")
    print(f"REST API base URL:    {result.api_base_url}")
    print(f"Generated tools:      {result.operation_count}")
    print(f"MCP endpoint URL:     {result.mcp_url}")
    print(f"Run instructions:     {result.output_dir / 'README.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
