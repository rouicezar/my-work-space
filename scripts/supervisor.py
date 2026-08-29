#!/usr/bin/env python3
"""Versioned process protocol between the native app and product Supervisor."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import preflight


SCHEMA_VERSION = 1


class ProtocolArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def envelope(
    *,
    command: str,
    request_id: str,
    status: str,
    payload: dict[str, Any] | None = None,
    error: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "request_id": request_id,
        "status": status,
        "payload": payload,
        "error": error,
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }


def parser() -> argparse.ArgumentParser:
    result = ProtocolArgumentParser(description=__doc__)
    result.add_argument("--request-id", required=True)
    commands = result.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("preflight")
    probe.add_argument(
        "--profiles",
        type=Path,
        default=REPOSITORY_ROOT / "config/hardware-profiles.yaml",
    )
    probe.add_argument("--check-path", type=Path, required=True)
    probe.add_argument("--ports", type=int, nargs="*", default=list(preflight.DEFAULT_PORTS))
    return result


def validate_request_id(value: str) -> str:
    parsed = uuid.UUID(value)
    if str(parsed) != value.lower():
        raise ValueError("request ID must use canonical UUID form")
    return str(parsed)


def run(args: argparse.Namespace) -> dict[str, Any]:
    request_id = validate_request_id(args.request_id)
    if args.command == "preflight":
        if not args.profiles.is_absolute() or not args.check_path.is_absolute():
            raise ValueError("preflight paths must be absolute")
        if not args.check_path.is_dir():
            raise ValueError("preflight check path must be an existing directory")
        if len(args.ports) != len(set(args.ports)) or any(
            port < 1024 or port > 65535 for port in args.ports
        ):
            raise ValueError("preflight ports must be unique unprivileged TCP ports")
        report = preflight.build_report(args.profiles, args.check_path, tuple(args.ports))
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload=report,
        )
    raise ValueError("unsupported command")


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    command = next((item for item in ("preflight",) if item in raw), "unknown")
    request_id = "invalid"
    if "--request-id" in raw:
        index = raw.index("--request-id") + 1
        if index < len(raw):
            request_id = raw[index]
    try:
        args = parser().parse_args(raw)
        response = run(args)
        exit_code = 0
    except (OSError, ValueError, json.JSONDecodeError):
        response = envelope(
            command=command,
            request_id=request_id,
            status="error",
            error={
                "code": "SUPERVISOR_COMMAND_FAILED",
                "message": "Supervisor command could not complete.",
            },
        )
        exit_code = 2
    print(json.dumps(response, ensure_ascii=False, separators=(",", ":")))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
