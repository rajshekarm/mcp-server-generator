"""Start PolicyCenter, ClaimCenter, and BillingCenter together."""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Center:
    name: str
    module: str
    port: int


CENTERS = (
    Center("PolicyCenter", "sample_rest_apis.policy_center.app:app", 8111),
    Center("ClaimCenter", "sample_rest_apis.claim_center.app:app", 8112),
    Center("BillingCenter", "sample_rest_apis.billing_center.app:app", 8113),
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start all insurance center REST APIs."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface used by every API (default: 127.0.0.1).",
    )
    return parser.parse_args()


def ensure_ports_available(host: str) -> None:
    unavailable: list[int] = []

    for center in CENTERS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, center.port))
            except OSError:
                unavailable.append(center.port)

    if unavailable:
        ports = ", ".join(str(port) for port in unavailable)
        raise RuntimeError(f"Cannot start because these ports are in use: {ports}")


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
    args = parse_args()
    ensure_ports_available(args.host)

    processes: list[subprocess.Popen[bytes]] = []

    try:
        for center in CENTERS:
            command = [
                sys.executable,
                "-m",
                "uvicorn",
                center.module,
                "--host",
                args.host,
                "--port",
                str(center.port),
            ]
            process = subprocess.Popen(command, cwd=REPOSITORY_ROOT)
            processes.append(process)

            print(
                f"Started {center.name:<13} "
                f"PID={process.pid} "
                f"Docs=http://{args.host}:{center.port}/docs"
            )

        print("\nAll insurance centers are running. Press Ctrl+C to stop them.\n")

        while True:
            for center, process in zip(CENTERS, processes, strict=True):
                exit_code = process.poll()
                if exit_code is not None:
                    print(f"{center.name} stopped unexpectedly with code {exit_code}.")
                    return exit_code or 1
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping all insurance centers...")
        return 0
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
