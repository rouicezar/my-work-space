#!/usr/bin/env python3
"""Single product-owned MCP surface for Qwen Agent tool requests."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.herdr_tool_bridge import HerdrToolBridge  # noqa: E402


TOOL_NAME = "forma_governed_tool"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, required=True)
    result.add_argument("--repository-root", type=Path, required=True)
    result.add_argument("--catalog", type=Path, required=True)
    return result


def _response(request_id: object, *, result: object = None, error: object = None) -> None:
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error is None:
        payload["result"] = result
    else:
        payload["error"] = error
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _tool_definition() -> dict[str, object]:
    return {
        "name": TOOL_NAME,
        "description": "Request one capability through Forma policy, approval, and audit.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["capability_id", "operation", "arguments", "data_classes"],
            "properties": {
                "capability_id": {"type": "string"},
                "operation": {"type": "string"},
                "arguments": {"type": "object"},
                "data_classes": {"type": "array", "items": {"type": "string"}},
            },
        },
    }


def run(arguments: argparse.Namespace) -> int:
    correlation_id = os.environ.get("FORMA_TASK_CORRELATION_ID", "")
    workspace = Path(os.environ.get("FORMA_TASK_WORKSPACE", ""))
    bridge = HerdrToolBridge(repository_root=arguments.repository_root)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            if method == "initialize":
                _response(request_id, result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "forma-governed-tools", "version": "0.1.0"},
                })
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                _response(request_id, result={"tools": [_tool_definition()]})
            elif method == "tools/call":
                params = request.get("params", {})
                values = params.get("arguments", {}) if isinstance(params, dict) else {}
                if params.get("name") != TOOL_NAME or not isinstance(values, dict):
                    raise ValueError("unsupported tool call")
                classes = values.get("data_classes")
                if not isinstance(classes, list) or any(not isinstance(item, str) for item in classes):
                    raise ValueError("data_classes must be an array of strings")
                call_arguments = values.get("arguments")
                if not isinstance(call_arguments, dict):
                    raise ValueError("arguments must be an object")
                artifact = bridge.call(
                    product_root=arguments.root,
                    correlation_id=correlation_id,
                    capability_id=str(values.get("capability_id", "")),
                    operation=str(values.get("operation", "")),
                    arguments=call_arguments,
                    data_classes=frozenset(classes),
                    catalog_path=arguments.catalog,
                    workspace_dir=workspace,
                )
                _response(request_id, result={
                    "content": [{"type": "text", "text": artifact.text}],
                    "isError": artifact.is_error,
                })
            else:
                _response(request_id, error={"code": -32601, "message": "method not found"})
        except Exception as exc:
            _response(request.get("id") if isinstance(request, dict) else None,
                      error={"code": -32602, "message": str(exc)})
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parser().parse_args()))
