import json
import io
import unittest
from typing import Any

from forma_ai.mcp_client import (
    MCPClient,
    MCPClientError,
    MCPServerSpec,
    NewlineDelimitedJsonRpcTransport,
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

    def test_newline_delimited_transport_roundtrip(self) -> None:
        payload = {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
        body = json.dumps(payload).encode("utf-8") + b"\n"
        reader = io.BytesIO(body)
        writer = io.BytesIO()
        transport = NewlineDelimitedJsonRpcTransport(reader, writer)
        transport.write({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}})
        written = writer.getvalue()
        self.assertNotIn(b"Content-Length:", written)
        self.assertEqual(written.count(b"\n"), 1)
        self.assertEqual(transport.read(), payload)

    def test_newline_transport_rejects_malformed_stdout(self) -> None:
        transport = NewlineDelimitedJsonRpcTransport(io.BytesIO(b"not-json\n"), io.BytesIO())
        with self.assertRaises(MCPClientError) as raised:
            transport.read()
        self.assertEqual(raised.exception.code, "MCP_FRAME_INVALID")

    def test_initialize_validates_protocol_and_capabilities(self) -> None:
        class InvalidInitializeServer(FakeServer):
            def handle(self, payload: dict[str, Any]) -> dict[str, Any] | None:
                response = super().handle(payload)
                if payload.get("method") == "initialize" and response is not None:
                    response["result"]["protocolVersion"] = "2099-01-01"
                return response

        client = MCPClient(FakeTransport(InvalidInitializeServer()))
        with self.assertRaises(MCPClientError) as raised:
            client.connect()
        self.assertEqual(raised.exception.code, "MCP_PROTOCOL_UNSUPPORTED")

    def test_request_skips_notifications_and_unrelated_response_ids(self) -> None:
        class CorrelatingTransport(FakeTransport):
            def write(self, payload: dict[str, Any]) -> None:
                if payload.get("method") == "initialize":
                    self._responses.extend([
                        {"jsonrpc": "2.0", "method": "notifications/progress", "params": {}},
                        {"jsonrpc": "2.0", "id": 999, "result": {}},
                    ])
                super().write(payload)

        client = MCPClient(CorrelatingTransport(FakeServer()))
        result = client.connect()
        self.assertEqual(result["serverInfo"]["name"], "fixture")

    def test_timeout_sends_request_cancellation(self) -> None:
        class TimeoutTransport:
            def __init__(self) -> None:
                self.writes: list[dict[str, Any]] = []

            def write(self, payload: dict[str, Any]) -> None:
                self.writes.append(payload)

            def read(self) -> dict[str, Any]:
                raise MCPClientError("MCP_TRANSPORT_TIMEOUT", "timed out")

            def close(self) -> None:
                pass

        transport = TimeoutTransport()
        client = MCPClient(transport)
        with self.assertRaises(MCPClientError) as raised:
            client.connect()
        self.assertEqual(raised.exception.code, "MCP_REQUEST_TIMEOUT")
        self.assertEqual(transport.writes[-1]["method"], "notifications/cancelled")
        self.assertEqual(transport.writes[-1]["params"]["requestId"], 1)

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
