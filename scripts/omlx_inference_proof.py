#!/usr/bin/env python3
"""Prove real local inference through the pinned oMLX runtime.

This is the P5-T05 acceptance command. It starts the installed oMLX runtime
with a product-isolated HOME, waits for it to serve a linked model, runs one
real chat completion, and records the generated text. A successful run proves
real local inference; a green ``/health`` alone never counts.

The oMLX API key is read only from the environment name supplied by
``--api-key-env`` (default ``OMLX_API_KEY``) and is never printed or logged.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.adapters.omlx import AdapterError, UrllibTransport
from forma_ai.installer import OMLXInstallLayout
from forma_ai.processes import omlx_process_spec
from forma_ai.runtime import SubprocessController

DEFAULT_PORT = 8000
PROMPT = "Reply with the exact text: FORMA_OK"


def resolve_executable(root: Path) -> Path:
    layout = OMLXInstallLayout(root)
    if not layout.active_record.is_file() or layout.active_record.is_symlink():
        raise SystemExit("oMLX is not installed; run scripts/install_omlx.py first")
    try:
        record = json.loads(layout.active_record.read_text(encoding="utf-8"))
        app = Path(record["app_path"])
    except (KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("oMLX active record is invalid") from exc
    executable = app / "Contents/MacOS/omlx-cli"
    if not executable.is_file() or executable.is_symlink() or not os.access(executable, os.X_OK):
        raise SystemExit("oMLX runtime executable is missing or unsafe")
    return executable


def list_models(transport: UrllibTransport) -> list[str]:
    result = transport.request("GET", "/v1/models")
    raw = result.body.get("data")
    if not isinstance(raw, list):
        raise AdapterError("INVALID_MODELS", "/v1/models did not return a data list")
    models = [
        entry["id"]
        for entry in raw
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    ]
    if not models:
        raise AdapterError("NO_MODELS", "/v1/models listed no models")
    return models


def select_model(transport: UrllibTransport, requested: str | None) -> str:
    models = list_models(transport)
    if requested:
        for candidate in models:
            if candidate == requested or candidate.endswith(f"/{requested}"):
                return candidate
        raise AdapterError("MODEL_NOT_FOUND", requested)
    return models[0]


def evaluate_completion(response: dict[str, Any], requested_model: str) -> dict[str, Any]:
    """Reduce an oMLX completion body to honest proof evidence (pure/testable)."""
    http_status = int(response.get("http_status", 0))
    choices = response.get("body", {}).get("choices")
    if not isinstance(choices, list) or not choices:
        return {"status": "proof_failed", "reason": "no_choices", "http_status": http_status}
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message")
    content = str(message.get("content") or "") if isinstance(message, dict) else ""
    finish_reason = first.get("finish_reason")
    usage = response.get("body", {}).get("usage") or {}
    ok = http_status == 200 and bool(content.strip())
    return {
        "status": "proof_passed" if ok else "proof_failed",
        "reason": None if ok else ("empty_content" if http_status == 200 else "http_error"),
        "http_status": http_status,
        "model": first.get("model") or requested_model,
        "finish_reason": finish_reason,
        "content": content,
        "usage": usage,
    }


def wait_ready(transport: UrllibTransport, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error = "timeout"
    while time.monotonic() < deadline:
        try:
            health = transport.request("GET", "/health")
            status = str(health.body.get("status", "")).lower()
            if health.status == 200 and status in {"ok", "healthy"}:
                list_models(transport)
                return
            last_error = f"health status {status or health.status}"
        except AdapterError as exc:
            last_error = exc.code
        time.sleep(0.25)
    raise SystemExit(f"oMLX server did not become ready before timeout (last: {last_error})")


def kill_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--model", default=None, help="model id or suffix; defaults to first listed")
    parser.add_argument("--api-key-env", default="OMLX_API_KEY")
    parser.add_argument("--start-timeout", type=float, default=60.0)
    parser.add_argument("--completion-timeout", type=float, default=120.0)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env, "")
    if len(api_key) < 32:
        raise SystemExit(f"a >=32-character local API key is required via {args.api_key_env}")
    if not args.root.is_absolute():
        raise SystemExit("--root must be an absolute path")

    executable = resolve_executable(args.root)
    spec = omlx_process_spec(executable=executable, app_support=args.root, port=args.port)
    for path in (Path(spec.working_directory), Path(spec.environment["HOME"]), Path(spec.environment["TMPDIR"])):
        path.mkdir(parents=True, exist_ok=True)
    environment = dict(spec.environment)
    environment["OMLX_API_KEY"] = api_key

    controller = SubprocessController()
    log_path = args.root / "logs/omlx/proof.log"
    launcher = controller.spawn(
        role="omlx",
        executable=spec.executable,
        arguments=spec.arguments,
        environment=environment,
        working_directory=spec.working_directory,
        log_path=log_path,
    )

    transport = UrllibTransport(f"http://127.0.0.1:{args.port}", api_key=api_key, timeout=args.completion_timeout)
    try:
        wait_ready(transport, args.start_timeout)
        model = select_model(transport, args.model)
        completion = transport.request(
            "POST",
            "/v1/chat/completions",
            {
                "model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                "temperature": 0,
                "max_tokens": 16,
                "stream": False,
            },
        )
        evidence = evaluate_completion(
            {"http_status": completion.status, "body": completion.body}, model
        )
    finally:
        kill_group(launcher.pid)

    result = {
        "schema_version": 1,
        "component": "omlx",
        "prompt": PROMPT,
        "port": args.port,
        "executable": str(executable),
        **evidence,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if evidence["status"] == "proof_passed" else 1


if __name__ == "__main__":
    sys.exit(main())
