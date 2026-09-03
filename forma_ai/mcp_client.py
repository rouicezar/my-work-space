"""Thin MCP client host over JSON-RPC content-length stdio framing."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, BinaryIO, Callable, Mapping, Protocol


MCP_PROTOCOL_VERSION = "2024-11-05"
CLIENT_NAME = "forma-ai"
CLIENT_VERSION = "0.1"


class MCPClientError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class MCPServerSpec:
    command: str
    args: tuple[str, ...] = ()
    env: Mapping[str, str] | None = None

    def argv(self) -> list[str]:
        if not self.command:
            raise MCPClientError("MCP_COMMAND_INVALID", "server command is required")
        return [self.command, *self.args]


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class MCPToolCallResult:
    content: tuple[dict[str, Any], ...]
    is_error: bool


class MCPTransport(Protocol):
    def write(self, payload: dict[str, Any]) -> None: ...
    def read(self) -> dict[str, Any]: ...
    def close(self) -> None: ...


RequestCallable = Callable[[str, dict[str, Any]], dict[str, Any]]


class FramedJsonRpcTransport:
    """Content-Length framed JSON-RPC over binary streams."""

    def __init__(self, reader: BinaryIO, writer: BinaryIO) -> None:
        self._reader = reader
        self._writer = writer

    def write(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self._writer.write(header + body)
        self._writer.flush()

    def read(self) -> dict[str, Any]:
        headers: dict[str, str] = {}
        while True:
            line = self._reader.readline()
            if not line:
                raise MCPClientError("MCP_TRANSPORT_EOF", "server closed stdout")
            stripped = line.strip()
            if not stripped:
                break
            key, value = stripped.decode("ascii").split(":", 1)
            headers[key.strip().lower()] = value.strip()
        try:
            length = int(headers["content-length"])
        except (KeyError, ValueError) as exc:
            raise MCPClientError("MCP_FRAME_INVALID", "missing content-length") from exc
        body = self._reader.read(length)
        if len(body) != length:
            raise MCPClientError("MCP_FRAME_INVALID", "truncated message body")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise MCPClientError("MCP_FRAME_INVALID", "message is not JSON") from exc
        if not isinstance(payload, dict):
            raise MCPClientError("MCP_FRAME_INVALID", "message must be an object")
        return payload

    def close(self) -> None:
        try:
            self._writer.close()
        finally:
            self._reader.close()


class MCPClient:
    """Minimal MCP host for initialize, tools/list, and tools/call."""

    def __init__(
        self,
        transport: MCPTransport,
        *,
        request: RequestCallable | None = None,
    ) -> None:
        self._transport = transport
        self._request = request or self._default_request
        self._next_id = 1
        self._initialized = False

    @classmethod
    def from_server_spec(cls, spec: MCPServerSpec) -> MCPClient:
        process = subprocess.Popen(
            spec.argv(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=None if spec.env is None else dict(spec.env),
            text=False,
        )
        if process.stdin is None or process.stdout is None:
            raise MCPClientError("MCP_PROCESS_INVALID", "stdio pipes unavailable")
        transport = FramedJsonRpcTransport(process.stdout, process.stdin)
        client = cls(transport)
        client._process = process
        return client

    def connect(self) -> dict[str, Any]:
        if self._initialized:
            raise MCPClientError("MCP_ALREADY_CONNECTED", "session already initialized")
        result = self._request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
            },
        )
        self._notify("notifications/initialized", {})
        self._initialized = True
        return result

    def list_tools(self) -> list[MCPTool]:
        self._require_initialized()
        result = self._request("tools/list", {})
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise MCPClientError("MCP_TOOLS_INVALID", "tools/list result missing tools")
        parsed: list[MCPTool] = []
        for item in tools:
            if not isinstance(item, dict):
                raise MCPClientError("MCP_TOOLS_INVALID", "tool entry must be an object")
            name = item.get("name")
            description = item.get("description", "")
            schema = item.get("inputSchema", {})
            if not isinstance(name, str) or not name:
                raise MCPClientError("MCP_TOOLS_INVALID", "tool name is required")
            if not isinstance(description, str):
                raise MCPClientError("MCP_TOOLS_INVALID", "tool description must be a string")
            if not isinstance(schema, dict):
                raise MCPClientError("MCP_TOOLS_INVALID", "tool inputSchema must be an object")
            parsed.append(MCPTool(name=name, description=description, input_schema=schema))
        return parsed

    def call_tool(self, name: str, arguments: Mapping[str, Any] | None = None) -> MCPToolCallResult:
        self._require_initialized()
        if not name:
            raise MCPClientError("MCP_TOOL_NAME_INVALID", "tool name is required")
        payload = {"name": name, "arguments": dict(arguments or {})}
        result = self._request("tools/call", payload)
        content = result.get("content")
        is_error = result.get("isError", False)
        if not isinstance(content, list):
            raise MCPClientError("MCP_TOOL_RESULT_INVALID", "tools/call content must be a list")
        if not isinstance(is_error, bool):
            raise MCPClientError("MCP_TOOL_RESULT_INVALID", "tools/call isError must be boolean")
        blocks: list[dict[str, Any]] = []
        for item in content:
            if not isinstance(item, dict):
                raise MCPClientError("MCP_TOOL_RESULT_INVALID", "content block must be an object")
            blocks.append(item)
        return MCPToolCallResult(content=tuple(blocks), is_error=is_error)

    def close(self) -> None:
        self._transport.close()
        process = getattr(self, "_process", None)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

    def _require_initialized(self) -> None:
        if not self._initialized:
            raise MCPClientError("MCP_NOT_INITIALIZED", "call connect() first")

    def _default_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._transport.write(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
        )
        while True:
            message = self._transport.read()
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                code = "MCP_REQUEST_FAILED"
                detail = "request failed"
                if isinstance(error, dict):
                    code = str(error.get("code", code))
                    detail = str(error.get("message", detail))
                raise MCPClientError("MCP_REQUEST_FAILED", f"{code}: {detail}")
            result = message.get("result")
            if not isinstance(result, dict):
                raise MCPClientError("MCP_RESPONSE_INVALID", "result must be an object")
            return result

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        self._transport.write({"jsonrpc": "2.0", "method": method, "params": params})


def connect_stdio_server(spec: MCPServerSpec) -> MCPClient:
    client = MCPClient.from_server_spec(spec)
    client.connect()
    return client
