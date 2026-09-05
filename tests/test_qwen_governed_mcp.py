import os
import tempfile
import unittest
import uuid
from pathlib import Path

from forma_ai.mcp_client import MCPServerSpec, connect_stdio_server
from forma_ai.tool_registry import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


class QwenGovernedMCPTests(unittest.TestCase):
    def test_real_ndjson_server_lists_and_routes_echo_with_bound_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            product = base / "Product"
            workspace = base / "workspace"
            product.mkdir()
            workspace.mkdir()
            ToolRegistry(
                product, catalog_path=ROOT / "config/tool-packages.json",
                repository_root=ROOT,
            ).install("fixture-echo-mcp")
            correlation_id = str(uuid.uuid4())
            previous = os.environ.copy()
            os.environ.update({
                "FORMA_TASK_CORRELATION_ID": correlation_id,
                "FORMA_TASK_WORKSPACE": str(workspace),
            })
            client = connect_stdio_server(MCPServerSpec(
                command=os.sys.executable,
                args=(
                    str(ROOT / "scripts/qwen_governed_mcp.py"),
                    "--root", str(product), "--repository-root", str(ROOT),
                    "--catalog", str(ROOT / "config/tool-routing.json"),
                ),
            ))
            try:
                self.assertEqual([item.name for item in client.list_tools()], ["forma_governed_tool"])
                result = client.call_tool("forma_governed_tool", {
                    "capability_id": "echo.transform", "operation": "echo",
                    "arguments": {"text": "governed-qwen"},
                    "data_classes": ["tool_result"],
                })
            finally:
                client.close()
                os.environ.clear()
                os.environ.update(previous)
            self.assertFalse(result.is_error)
            self.assertIn("governed-qwen", result.content[0]["text"])
            audit = (product / "logs/audit/tools.jsonl").read_text(encoding="utf-8")
            self.assertIn(correlation_id, audit)


if __name__ == "__main__":
    unittest.main()
