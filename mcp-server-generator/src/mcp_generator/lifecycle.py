from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import urlparse

from .registry import ServerRegistry


class LifecycleError(RuntimeError):
    """Raised when an MCP server cannot be started or stopped safely."""


@dataclass
class ManagedProcess:
    process: subprocess.Popen[bytes]
    log_handle: BinaryIO
    started_at: str
    log_path: Path


class LifecycleManager:
    def __init__(self, registry: ServerRegistry, startup_timeout: float = 12.0) -> None:
        self.registry = registry
        self.startup_timeout = startup_timeout
        self._processes: dict[str, ManagedProcess] = {}
        self._last_exit_codes: dict[str, int] = {}
        self._last_errors: dict[str, str] = {}
        self._lock = threading.RLock()

    def list_servers(self) -> list[dict[str, Any]]:
        return [self.with_runtime(record) for record in self.registry.list()]

    def get_server(self, server_id: str) -> dict[str, Any]:
        return self.with_runtime(self.registry.get(server_id))

    def with_runtime(self, record: dict[str, Any]) -> dict[str, Any]:
        server_id = record["server"]["id"]
        with self._lock:
            managed = self._processes.get(server_id)
            if managed is not None:
                exit_code = managed.process.poll()
                if exit_code is not None:
                    self._last_exit_codes[server_id] = exit_code
                    self._close_log(managed)
                    del self._processes[server_id]
                    managed = None

            if managed is not None:
                runtime = {
                    "status": "running",
                    "pid": managed.process.pid,
                    "started_at": managed.started_at,
                    "exit_code": None,
                    "last_error": None,
                }
            else:
                exit_code = self._last_exit_codes.get(server_id)
                error = self._last_errors.get(server_id)
                host, port = _connection_target(record["connection"]["url"])
                externally_running = _port_is_open(host, port)
                runtime = {
                    "status": (
                        "external"
                        if externally_running
                        else "failed"
                        if error or (exit_code not in (None, 0))
                        else "stopped"
                    ),
                    "pid": None,
                    "started_at": None,
                    "exit_code": exit_code,
                    "last_error": error,
                }

        return {**record, "runtime": runtime}

    def start(self, server_id: str) -> dict[str, Any]:
        record = self.registry.get(server_id)
        with self._lock:
            existing = self._processes.get(server_id)
            if existing is not None and existing.process.poll() is None:
                raise LifecycleError(f"{server_id} is already running")

            mcp_url = record["connection"]["url"]
            host, port = _connection_target(mcp_url)
            if _port_is_open(host, port):
                raise LifecycleError(
                    f"Port {port} is already in use. The process was not started by this generator."
                )

            directory = Path(record["generation"]["output_directory"]).resolve()
            entrypoint = directory / "server.py"
            if not entrypoint.is_file():
                raise LifecycleError(f"Generated entrypoint is missing: {entrypoint}")

            logs_dir = directory / "logs"
            logs_dir.mkdir(exist_ok=True)
            log_path = logs_dir / "server.log"
            log_handle = log_path.open("ab", buffering=0)
            child_environment = os.environ.copy()
            for variable in ("MCP_HOST", "MCP_PORT", "MCP_PATH"):
                child_environment.pop(variable, None)

            try:
                process = subprocess.Popen(
                    [sys.executable, str(entrypoint)],
                    cwd=directory,
                    env=child_environment,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                )
            except OSError as exc:
                log_handle.close()
                self._last_errors[server_id] = str(exc)
                raise LifecycleError(f"Could not start {server_id}: {exc}") from exc

            managed = ManagedProcess(
                process=process,
                log_handle=log_handle,
                started_at=datetime.now(timezone.utc).isoformat(),
                log_path=log_path,
            )
            self._processes[server_id] = managed
            self._last_errors.pop(server_id, None)
            self._last_exit_codes.pop(server_id, None)

        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            exit_code = process.poll()
            if exit_code is not None:
                error = _tail_text(log_path)
                with self._lock:
                    self._last_exit_codes[server_id] = exit_code
                    self._last_errors[server_id] = error or f"Exited with code {exit_code}"
                    self._processes.pop(server_id, None)
                    self._close_log(managed)
                raise LifecycleError(
                    f"{server_id} exited during startup with code {exit_code}. Check its logs."
                )
            if _port_is_open(host, port):
                return self.get_server(server_id)
            time.sleep(0.15)

        self._terminate(managed)
        with self._lock:
            self._processes.pop(server_id, None)
            self._last_errors[server_id] = f"Startup timed out waiting for port {port}"
        raise LifecycleError(f"{server_id} did not open port {port} within the startup timeout")

    def stop(self, server_id: str) -> dict[str, Any]:
        record = self.registry.get(server_id)
        with self._lock:
            managed = self._processes.get(server_id)
            if managed is None or managed.process.poll() is not None:
                raise LifecycleError(
                    f"{server_id} is not running under the generator's control"
                )

        self._terminate(managed)
        with self._lock:
            # A deliberate terminate commonly has a non-zero OS exit code.
            # Record it as a clean lifecycle stop rather than a server failure.
            self._last_exit_codes[server_id] = 0
            self._last_errors.pop(server_id, None)
            self._processes.pop(server_id, None)
        return self.with_runtime(record)

    def stop_all(self) -> None:
        with self._lock:
            processes = list(self._processes.items())
        for server_id, managed in processes:
            self._terminate(managed)
            with self._lock:
                self._last_exit_codes[server_id] = 0
                self._processes.pop(server_id, None)

    def logs(self, server_id: str, max_bytes: int = 32_000) -> dict[str, Any]:
        record = self.registry.get(server_id)
        log_path = Path(record["generation"]["output_directory"]) / "logs" / "server.log"
        return {
            "server_id": server_id,
            "path": str(log_path),
            "content": _tail_text(log_path, max_bytes=max_bytes),
        }

    @staticmethod
    def _close_log(managed: ManagedProcess) -> None:
        if not managed.log_handle.closed:
            managed.log_handle.close()

    def _terminate(self, managed: ManagedProcess) -> None:
        if managed.process.poll() is None:
            managed.process.terminate()
            try:
                managed.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                managed.process.kill()
                managed.process.wait(timeout=5)
        self._close_log(managed)


def _connection_target(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port


def _port_is_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _tail_text(path: Path, max_bytes: int = 8_000) -> str:
    if not path.is_file():
        return ""
    with path.open("rb") as log_file:
        log_file.seek(0, 2)
        size = log_file.tell()
        log_file.seek(max(0, size - max_bytes))
        return log_file.read().decode("utf-8", errors="replace").strip()
