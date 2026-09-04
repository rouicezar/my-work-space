"""C1-T02 interoperability tests against the official MCP Python SDK."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from forma_ai.mcp_client import MCPServerSpec, connect_stdio_server


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_SERVER = ROOT / "tests/fixtures/mcp_official_sdk_server/server.py"


@unittest.skipUnless(importlib.util.find_spec("mcp"), "official MCP Python SDK is unavailable")
class OfficialMCPInteropTests(unittest.TestCase):
    def test_stdio_ndjson_connect_list_call_and_cleanup(self) -> None:
        client = connect_stdio_server(
            MCPServerSpec(command=sys.executable, args=(str(OFFICIAL_SERVER),)),
        )
        process = client._process
        try:
            tools = client.list_tools()
            self.assertEqual([tool.name for tool in tools], ["echo"])
            result = client.call_tool("echo", {"message": "你好 MCP"})
            self.assertFalse(result.is_error)
            self.assertIn("你好 MCP", str(result.content))
        finally:
            client.close()
        self.assertIsNotNone(process.returncode)


if __name__ == "__main__":
    unittest.main()
