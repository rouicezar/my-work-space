#!/usr/bin/env python3
"""Minimal stdio MCP workbook server for Forma AI end-to-end proof tests."""

from __future__ import annotations

import csv
import json
import sys
from html import escape
from pathlib import Path


def write_message(payload: dict[str, object]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    sys.stdout.buffer.flush()


def read_message() -> dict[str, object]:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            raise SystemExit(0)
        if line.strip() == b"":
            break
        key, value = line.decode("ascii").split(":", 1)
        headers[key.strip().lower()] = value.strip()
    length = int(headers["content-length"])
    payload = json.loads(sys.stdin.buffer.read(length))
    if not isinstance(payload, dict):
        raise ValueError("message must be an object")
    return payload


def merge_workbook(input_a: str, input_b: str, output_path: str) -> dict[str, object]:
    rows_a = list(csv.reader(Path(input_a).read_text(encoding="utf-8").splitlines()))
    rows_b = list(csv.reader(Path(input_b).read_text(encoding="utf-8").splitlines()))
    if not rows_a:
        raise ValueError(f"empty workbook: {input_a}")
    header = rows_a[0]
    merged = [header]
    merged.extend(rows_a[1:])
    for row in rows_b[1:] if rows_b else []:
        merged.append(row)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(merged)
    return {
        "output_path": str(output),
        "row_count": max(len(merged) - 1, 0),
        "columns": header,
    }


def render_html_report(input_path: str, output_path: str, title: str) -> dict[str, object]:
    rows = list(csv.reader(Path(input_path).read_text(encoding="utf-8").splitlines()))
    if not rows:
        raise ValueError(f"empty workbook: {input_path}")
    header = rows[0]
    body_rows = rows[1:]
    table_head = "".join(f"<th>{escape(cell)}</th>" for cell in header)
    table_body = "".join(
        "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
        for row in body_rows
    )
    html = (
        "<!DOCTYPE html><html><head>"
        f"<meta charset=\"utf-8\"><title>{escape(title)}</title>"
        "</head><body>"
        f"<h1>{escape(title)}</h1>"
        f"<table><thead><tr>{table_head}</tr></thead>"
        f"<tbody>{table_body}</tbody></table>"
        "</body></html>"
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return {
        "output_path": str(output),
        "title": title,
        "row_count": len(body_rows),
        "columns": header,
    }


TOOLS: dict[str, dict[str, object]] = {
    "merge_workbook": {
        "description": "Merge two CSV workbooks into one output CSV",
        "inputSchema": {
            "type": "object",
            "required": ["input_a", "input_b", "output_path"],
            "properties": {
                "input_a": {"type": "string", "description": "Path to first CSV workbook"},
                "input_b": {"type": "string", "description": "Path to second CSV workbook"},
                "output_path": {"type": "string", "description": "Path for merged CSV output"},
            },
        },
        "handler": merge_workbook,
    },
    "render_html_report": {
        "description": "Render a minimal HTML table report from a CSV workbook",
        "inputSchema": {
            "type": "object",
            "required": ["input_path", "output_path", "title"],
            "properties": {
                "input_path": {"type": "string", "description": "Path to source CSV workbook"},
                "output_path": {"type": "string", "description": "Path for HTML report output"},
                "title": {"type": "string", "description": "Report title"},
            },
        },
        "handler": render_html_report,
    },
}


def call_tool(name: str, arguments: dict[str, object]) -> dict[str, object]:
    tool = TOOLS.get(name)
    if tool is None:
        raise ValueError(f"unknown tool {name!r}")
    handler = tool["handler"]
    if not callable(handler):
        raise ValueError(f"tool {name!r} has no handler")
    result = handler(**arguments)
    return {
        "content": [{"type": "text", "text": json.dumps(result)}],
        "isError": False,
    }


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
                    "serverInfo": {"name": "fixture-workbook-mcp", "version": "1.0.0"},
                },
            })
            write_message({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            continue
        if method == "tools/list":
            write_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": name,
                            "description": tool["description"],
                            "inputSchema": tool["inputSchema"],
                        }
                        for name, tool in TOOLS.items()
                    ],
                },
            })
            continue
        if method == "tools/call":
            params = request.get("params", {})
            if not isinstance(params, dict):
                params = {}
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            try:
                result = call_tool(str(name), arguments)
            except Exception as exc:  # noqa: BLE001 - fixture server returns tool errors inline
                result = {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                }
            write_message({"jsonrpc": "2.0", "id": request_id, "result": result})
            continue
        if request_id is not None:
            write_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"unknown method {method!r}"},
            })


if __name__ == "__main__":
    main()
