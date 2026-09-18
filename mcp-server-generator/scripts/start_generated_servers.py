"""Discover and start every MCP server under the generated directory."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = PACKAGE_ROOT / "generated"

ENV_PORT_PATTERN = re.compile(
    r"port\s*=\s*int\(os\.getenv\(\s*['\"]MCP_PORT['\"]\s*,\s*['\"](\d+)['\"]\s*\)\s*\)"
)
FIXED_PORT_PATTERN = re.compile(r"port\s*=\s*(\d+)")


@dataclass(frozen=True)
class GeneratedServer:
    name: str
    directory: Path
    entrypoint: Path
    port: int


def read_configured_port(entrypoint: Path) -> int:
    source = entrypoint.read_text(encoding="utf-8")

    for pattern in (ENV_PORT_PATTERN, FIXED_PORT_PATTERN):
        match = pattern.search(source)
        if match:
            return int(match.group(1))

    raise RuntimeError(f"Could not determine the configured port in {entrypoint}")


def discover_servers() -> list[GeneratedServer]:
    if not GENERATED_ROOT.is_dir():
        raise RuntimeError(f"Generated-server directory does not exist: {GENERATED_ROOT}")

    servers = [
        GeneratedServer(
            name=entrypoint.parent.name,
            directory=entrypoint.parent,
            entrypoint=entrypoint,
            port=read_configured_port(entrypoint),
        )
        for entrypoint in sorted(GENERATED_ROOT.glob("*/server.py"))
    ]

    if not servers:
        raise RuntimeError(f"No generated server.py files were found under {GENERATED_ROOT}")

    servers_by_port: dict[int, list[str]] = {}
    for server in servers:
        servers_by_port.setdefault(server.port, []).append(server.name)

    conflicts = {
        port: names for port, names in servers_by_port.items() if len(names) > 1
    }
    if conflicts:
        details = "; ".join(
            f"port {port}: {', '.join(names)}"
            for port, names in sorted(conflicts.items())
        )
        raise RuntimeError(f"Generated servers have duplicate ports: {details}")

    return servers


def stop_processes(processes: list[subprocess.Popen[bytes]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()

    for process in processes:
        if process.poll() is not None:
            continue
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> int:
    servers = discover_servers()
    processes: list[subprocess.Popen[bytes]] = []

    # Use the ports configured in each generated server, even if the parent
    # terminal still has MCP environment variables from a previous run.
    child_environment = os.environ.copy()
    child_environment.pop("MCP_HOST", None)
    child_environment.pop("MCP_PORT", None)
    child_environment.pop("MCP_PATH", None)

    try:
        for server in servers:
            process = subprocess.Popen(
                [sys.executable, str(server.entrypoint)],
                cwd=server.directory,
                env=child_environment,
            )
            processes.append(process)
            print(
                f"Started {server.name:<35} "
                f"PID={process.pid} "
                f"URL=http://127.0.0.1:{server.port}/mcp"
            )

        print("\nAll generated MCP servers are running. Press Ctrl+C to stop them.\n")

        while True:
            for server, process in zip(servers, processes, strict=True):
                exit_code = process.poll()
                if exit_code is not None:
                    print(f"{server.name} stopped unexpectedly with code {exit_code}.")
                    return exit_code or 1
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping all generated MCP servers...")
        return 0
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
