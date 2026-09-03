import json
import io
import unittest
from typing import Any

from forma_ai.mcp_client import (
    FramedJsonRpcTransport,
    MCPClient,
    MCPClientError,
    MCPServerSpec,
)


class FakeServer:
    def __init__(self) -> None:
        self.tools = [
            {
                "name": "echo",
                "description": "Echo arguments",
                "inputSchema": {"type": "object", "properties": {"message": {"type": "string"}}},
            }
        ]
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def handle(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        method = payload.get("method")
        params = payload.get("params", {})
        request_id = payload.get("id")
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "fixture", "version": "0.0.1"},
                },
            }
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": self.tools}}
        if method == "tools/call":
            self.calls.append((params["name"], params["arguments"]))
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(params["arguments"])}],
                    "isError": False,
                },
            }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"unknown method {method}"},
        }


class FakeTransport:
    def __init__(self, server: FakeServer) -> None:
        self.server = server
        self.closed = False
        self._responses: list[dict[str, Any]] = []

    def write(self, payload: dict[str, Any]) -> None:
        response = self.server.handle(payload)
        if response is not None:
            self._responses.append(response)

    def read(self) -> dict[str, Any]:
        if not self._responses:
            raise MCPClientError("MCP_TRANSPORT_EOF", "no pending response")
        return self._responses.pop(0)

    def close(self) -> None:
        self.closed = True


class MCPClientTests(unittest.TestCase):
    def test_connect_list_tools_and_call_tool(self) -> None:
        server = FakeServer()
        transport = FakeTransport(server)
        client = MCPClient(transport)
        result = client.connect()
        self.assertEqual(result["protocolVersion"], "2024-11-05")
        tools = client.list_tools()
        self.assertEqual([tool.name for tool in tools], ["echo"])
        call = client.call_tool("echo", {"message": "hello"})
        self.assertFalse(call.is_error)
        self.assertEqual(call.content[0]["text"], '{"message": "hello"}')
        self.assertEqual(server.calls, [("echo", {"message": "hello"})])
        client.close()
        self.assertTrue(transport.closed)

    def test_framed_transport_roundtrip(self) -> None:
        payload = {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
        body = json.dumps(payload).encode("utf-8")
        reader = io.BytesIO(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
        writer = io.BytesIO()
        transport = FramedJsonRpcTransport(reader, writer)
        transport.write({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}})
        written = writer.getvalue()
        self.assertIn(b"Content-Length:", written)
        self.assertEqual(transport.read(), payload)

    def test_call_tool_before_connect_fails_closed(self) -> None:
        client = MCPClient(FakeTransport(FakeServer()))
        with self.assertRaises(MCPClientError) as raised:
            client.list_tools()
        self.assertEqual(raised.exception.code, "MCP_NOT_INITIALIZED")

    def test_invalid_server_spec(self) -> None:
        with self.assertRaises(MCPClientError) as raised:
            MCPServerSpec(command="").argv()
        self.assertEqual(raised.exception.code, "MCP_COMMAND_INVALID")


if __name__ == "__main__":
    unittest.main()
