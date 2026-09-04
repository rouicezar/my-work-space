#!/usr/bin/env python3
"""Minimal stdio MCP echo server for Forma AI registry tests."""

from __future__ import annotations

import json
import sys


def write_message(payload: dict[str, object]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(body + b"\n")
    sys.stdout.buffer.flush()


def read_message() -> dict[str, object]:
    line = sys.stdin.buffer.readline()
    if not line:
        raise SystemExit(0)
    payload = json.loads(line)
    if not isinstance(payload, dict):
        raise ValueError("message must be an object")
    return payload


def main() -> None:
    while True:
        request = read_message()
        method = request.get("method")
        request_id = request.get("id")
        if method == "initialize":
            write_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "fixture-echo-mcp", "version": "1.0.0"},
                },
            })
            write_message({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            continue
        if method == "tools/list":
            write_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [{
                        "name": "echo",
                        "description": "Echo tool arguments",
                        "inputSchema": {"type": "object"},
                    }],
                },
            })
            continue
        if method == "tools/call":
            params = request.get("params", {})
            arguments = params.get("arguments", {}) if isinstance(params, dict) else {}
            write_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(arguments)}],
                    "isError": False,
                },
            })
            continue
        if request_id is not None:
            write_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"unknown method {method!r}"},
            })


if __name__ == "__main__":
    main()
