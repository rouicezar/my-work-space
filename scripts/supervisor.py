#!/usr/bin/env python3
"""Versioned process protocol between the native app and product Supervisor."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import preflight
from mac_ai_work_os.artifacts import load_component, select_artifact, verify_file
from mac_ai_work_os.downloads import ResumableDownloader
from mac_ai_work_os.installer import OMLXInstallLayout, OMLXInstaller
from mac_ai_work_os.lifecycle import LifecycleJournal
from mac_ai_work_os.models import (
    huggingface_snapshot,
    link_external_model,
    load_model,
    verify_snapshot,
)


SCHEMA_VERSION = 1
DEFAULT_UPSTREAMS = REPOSITORY_ROOT / "config/upstreams.json"
DEFAULT_MODELS = REPOSITORY_ROOT / "config/models.json"
DEFAULT_MODEL_ID = "qwen3-0.6b-4bit-alpha"


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
    for name in ("installation-plan", "installation-status", "install-omlx"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        if name != "installation-status":
            command.add_argument("--os-major", type=int, required=True)
            command.add_argument("--upstreams", type=Path, default=DEFAULT_UPSTREAMS)
        if name == "install-omlx":
            command.add_argument("--approve-artifact-sha256", required=True)
    for name in ("model-plan", "link-model"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--cache-root", type=Path, required=True)
        command.add_argument("--catalog", type=Path, default=DEFAULT_MODELS)
        command.add_argument("--model-id", default=DEFAULT_MODEL_ID)
        if name == "link-model":
            command.add_argument("--approve-revision", required=True)
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
    if args.command in {"installation-plan", "installation-status", "install-omlx"}:
        _validate_product_root(args.root)
    if args.command in {"model-plan", "link-model"}:
        _validate_product_root(args.root)
        if not args.cache_root.is_absolute() or not args.cache_root.is_dir():
            raise ValueError("model cache root must be an existing absolute directory")
        if not args.catalog.is_absolute() or not args.catalog.is_file():
            raise ValueError("model catalog must be an existing absolute file")
        model = load_model(args.catalog, args.model_id)
        snapshot = huggingface_snapshot(args.cache_root, model)
        if args.command == "model-plan":
            try:
                verified = verify_snapshot(args.cache_root, model)
                available = True
                reason = None
            except Exception as exc:
                verified = snapshot
                available = False
                reason = getattr(exc, "code", "MODEL_UNAVAILABLE")
            return envelope(
                command=args.command,
                request_id=request_id,
                status="ok",
                payload={
                    "schema_version": 1,
                    "model_id": model.id,
                    "repository": model.repository,
                    "revision": model.revision,
                    "license": model.license,
                    "quantization_bits": model.quantization_bits,
                    "size_bytes": sum(item.size_bytes for item in model.files.values()),
                    "source_path": str(verified),
                    "available_verified": available,
                    "unavailable_reason": reason,
                    "approval_required": True,
                },
            )
        if args.approve_revision != model.revision:
            raise ValueError("model approval does not match selected revision")
        reference = link_external_model(
            product_root=args.root,
            cache_root=args.cache_root,
            model=model,
        )
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={"schema_version": 1, "reference": asdict(reference)},
        )
    if args.command == "installation-status":
        journal = LifecycleJournal(OMLXInstallLayout(args.root).operations)
        state = journal.load_optional()
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={
                "schema_version": 1,
                "component": "omlx",
                "operation": asdict(state) if state else None,
            },
        )
    if args.command in {"installation-plan", "install-omlx"}:
        if args.os_major < 15 or args.os_major > 99:
            raise ValueError("unsupported macOS major version")
        if not args.upstreams.is_absolute() or not args.upstreams.is_file():
            raise ValueError("upstream manifest must be an existing absolute file")
        expected = select_artifact(
            load_component(args.upstreams, "omlx"),
            platform="macos",
            os_major=args.os_major,
        )
        layout = OMLXInstallLayout(args.root)
        if args.command == "installation-plan":
            cached = layout.downloads / expected.name
            partial = layout.downloads / f"{expected.name}.part"
            cached_bytes = 0
            cached_verified = False
            cache_blocker = None
            if cached.is_file() and not cached.is_symlink():
                cached_verified = verify_file(cached, expected).valid
                if cached_verified:
                    cached_bytes = expected.size_bytes
                else:
                    cache_blocker = "DESTINATION_INVALID"
            partial_bytes = (
                partial.stat().st_size if partial.is_file() and not partial.is_symlink() else 0
            )
            active = _matches_active_bundle(layout, expected.release, expected.sha256)
            return envelope(
                command=args.command,
                request_id=request_id,
                status="ok",
                payload={
                    "schema_version": 1,
                    "component": "omlx",
                    "release": expected.release,
                    "artifact_name": expected.name,
                    "artifact_size_bytes": expected.size_bytes,
                    "artifact_sha256": expected.sha256,
                    "downloaded_bytes": min(max(cached_bytes, partial_bytes), expected.size_bytes),
                    "cached_artifact_verified": cached_verified,
                    "cache_blocker": cache_blocker,
                    "product_root": str(args.root),
                    "already_active": active,
                    "approval_required": True,
                },
            )
        if args.approve_artifact_sha256 != expected.sha256:
            raise ValueError("installation approval does not match selected artifact")
        installer = OMLXInstaller(
            layout,
            expected,
            downloader=ResumableDownloader(),
        )
        active = installer.run()
        return envelope(
            command=args.command,
            request_id=request_id,
            status="ok",
            payload={"schema_version": 1, "active": asdict(active)},
        )
    raise ValueError("unsupported command")


def _validate_product_root(root: Path) -> None:
    if not root.is_absolute():
        raise ValueError("product root must be absolute")
    resolved = root.resolve(strict=False)
    if resolved == Path("/") or resolved == Path.home() or root.is_symlink():
        raise ValueError("product root is unsafe")


def _matches_active_bundle(layout: OMLXInstallLayout, release: str, digest: str) -> bool:
    if not layout.active_record.is_file() or layout.active_record.is_symlink():
        return False
    try:
        record = json.loads(layout.active_record.read_text(encoding="utf-8"))
        app = Path(record["app_path"])
        return (
            record.get("schema_version") == 1
            and record.get("component") == "omlx"
            and record.get("release") == release
            and record.get("artifact_sha256") == digest
            and app == layout.app(release)
            and app.is_dir()
            and not app.is_symlink()
        )
    except (KeyError, OSError, TypeError, json.JSONDecodeError):
        return False


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    command = next(
        (
            item
            for item in (
                "preflight", "installation-plan", "installation-status", "install-omlx",
                "model-plan", "link-model",
            )
            if item in raw
        ),
        "unknown",
    )
    request_id = "invalid"
    if "--request-id" in raw:
        index = raw.index("--request-id") + 1
        if index < len(raw):
            request_id = raw[index]
    try:
        args = parser().parse_args(raw)
        response = run(args)
        exit_code = 0
    except Exception:
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
