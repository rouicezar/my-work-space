#!/usr/bin/env python3
"""Read-only compatibility probe for Mac AI Work OS."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


GIB = 1024**3
DEFAULT_PORTS = (8000,)


@dataclass(frozen=True)
class ProbeValue:
    value: Any | None
    error: str | None = None


def command_value(args: list[str]) -> ProbeValue:
    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        return ProbeValue(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        return ProbeValue(None, detail.strip())


def macos_version() -> ProbeValue:
    result = command_value(["sw_vers", "-productVersion"])
    if result.value:
        return result
    fallback = platform.mac_ver()[0]
    return ProbeValue(fallback or None, result.error)


def memory_bytes() -> ProbeValue:
    result = command_value(["sysctl", "-n", "hw.memsize"])
    if not result.value:
        return result
    try:
        return ProbeValue(int(result.value))
    except ValueError:
        return ProbeValue(None, f"unexpected hw.memsize value: {result.value!r}")


def free_disk_bytes(path: Path) -> ProbeValue:
    try:
        return ProbeValue(shutil.disk_usage(path).free)
    except OSError as exc:
        return ProbeValue(None, str(exc))


def port_available(port: int) -> ProbeValue:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        return ProbeValue(True)
    except OSError as exc:
        return ProbeValue(False, str(exc))
    finally:
        sock.close()


def load_profiles(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("profiles"), list):
        raise ValueError("unsupported hardware profile schema")
    return data["profiles"]


def choose_profile(
    profiles: list[dict[str, Any]], memory: int | None, free_disk: int | None
) -> dict[str, Any] | None:
    if memory is None or free_disk is None:
        return None
    eligible = [
        profile
        for profile in profiles
        if memory >= int(profile["minimum_memory_gib"]) * GIB
        and free_disk >= int(profile["minimum_free_disk_gib"]) * GIB
    ]
    return max(eligible, key=lambda item: int(item["minimum_memory_gib"]), default=None)


def build_report(profile_path: Path, check_path: Path, ports: tuple[int, ...]) -> dict[str, Any]:
    architecture = platform.machine()
    version = macos_version()
    memory = memory_bytes()
    disk = free_disk_bytes(check_path)
    port_results = {str(port): asdict(port_available(port)) for port in ports}
    profiles = load_profiles(profile_path)
    selected = choose_profile(profiles, memory.value, disk.value)

    blockers: list[dict[str, str]] = []
    unknowns: list[dict[str, str]] = []
    if architecture != "arm64":
        blockers.append({"code": "UNSUPPORTED_ARCH", "message": "Apple Silicon arm64 is required."})
    if not version.value:
        unknowns.append({"code": "MACOS_UNKNOWN", "message": version.error or "macOS version unavailable"})
    if memory.value is None:
        unknowns.append({"code": "MEMORY_UNKNOWN", "message": memory.error or "memory unavailable"})
    if disk.value is None:
        unknowns.append({"code": "DISK_UNKNOWN", "message": disk.error or "disk unavailable"})
    if memory.value is not None and memory.value < 16 * GIB:
        blockers.append({"code": "INSUFFICIENT_MEMORY", "message": "At least 16 GiB is provisionally required."})
    if disk.value is not None and disk.value < 40 * GIB:
        blockers.append({"code": "INSUFFICIENT_DISK", "message": "At least 40 GiB free is provisionally required."})
    for port, result in port_results.items():
        if not result["value"]:
            blockers.append({"code": "PORT_IN_USE", "message": f"Required port {port} is unavailable."})
    if selected is None and not blockers and not unknowns:
        blockers.append({"code": "NO_PROFILE", "message": "No compatible hardware profile was found."})

    status = "unsupported" if blockers else "unknown" if unknowns else "supported"
    return {
        "schema_version": 1,
        "status": status,
        "host": {
            "architecture": {"value": architecture, "error": None},
            "macos_version": asdict(version),
            "memory_bytes": asdict(memory),
            "free_disk_bytes": asdict(disk),
            "ports": port_results,
        },
        "selected_profile": selected,
        "blockers": blockers,
        "unknowns": unknowns,
        "notice": "Profile thresholds are provisional until multi-machine benchmarks pass.",
    }


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles", type=Path, default=root / "config/hardware-profiles.yaml")
    parser.add_argument("--check-path", type=Path, default=root)
    parser.add_argument("--ports", type=int, nargs="*", default=list(DEFAULT_PORTS))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.profiles, args.check_path, tuple(args.ports))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_version": 1, "status": "error", "error": str(exc)}))
        return 3
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"supported": 0, "unknown": 2, "unsupported": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
