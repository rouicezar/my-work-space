import json
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from forma_ai.broker import MemoryAuditSink
from forma_ai.mcp_client import MCPToolCallResult
from forma_ai.tool_registry import ToolRegistry
from forma_ai.tool_routing import (
    ToolApprovalStore,
    ToolCapabilityRequest,
    ToolRouter,
    ToolRoutingError,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config/tool-routing.json"
TOOL_CATALOG = ROOT / "config/tool-packages.json"


class ToolRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.product_root = Path(self.tempdir.name) / "Product"
        self.product_root.mkdir()
        self.now = datetime(2026, 9, 3, 10, tzinfo=timezone.utc)
        self.registry = ToolRegistry(
            self.product_root,
            catalog_path=TOOL_CATALOG,
            repository_root=ROOT,
        )
        self.registry.install("fixture-echo-mcp")
        self.audit = MemoryAuditSink()
        self.approvals = ToolApprovalStore(self.product_root)
        self.caller = Mock()
        self.caller.call_tool.return_value = MCPToolCallResult(
            content=({"type": "text", "text": "ok"},),
            is_error=False,
        )
        self.router = ToolRouter(
            self.registry,
            catalog_path=CATALOG,
            approvals=self.approvals,
            audit=self.audit,
            caller=self.caller,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request(self, **changes) -> ToolCapabilityRequest:
        values = {
            "correlation_id": str(uuid.uuid4()),
            "capability_id": "echo.transform",
            "operation": "echo",
            "arguments": {"message": "hello"},
            "data_classes": frozenset({"tool_result"}),
        }
        values.update(changes)
        return ToolCapabilityRequest(**values)

    def test_resolve_maps_capability_to_installed_tool(self) -> None:
        decision = self.router.resolve(self.request())
        self.assertEqual(decision.route, "ready")
        self.assertEqual(decision.tool_id, "fixture-echo-mcp")
        self.assertEqual(decision.mcp_tool_name, "echo")
        self.assertFalse(decision.approval_required)

    def test_resolve_reports_missing_tool(self) -> None:
        empty_root = Path(self.tempdir.name) / "Empty"
        empty_root.mkdir()
        router = ToolRouter(
            ToolRegistry(empty_root, catalog_path=TOOL_CATALOG, repository_root=ROOT),
            catalog_path=CATALOG,
            approvals=self.approvals,
            audit=self.audit,
        )
        decision = router.resolve(self.request())
        self.assertEqual(decision.route, "tool_missing")
        self.assertEqual(decision.reasons, ("tool_not_installed",))

    def test_low_sensitivity_executes_without_prior_approval(self) -> None:
        proposal, payload, preview = self.router.propose(self.request(), now=self.now)
        self.assertFalse(proposal.approval_required)
        self.assertFalse(preview.approval_required)
        result = self.router.execute(
            proposal, payload, arguments={"message": "hello"}, now=self.now,
        )
        self.assertFalse(result.is_error)
        self.caller.call_tool.assert_called_once()
        self.assertEqual(self.audit.events[-1]["event"], "tool_call")
        self.assertEqual(self.audit.events[-1]["outcome"], "completed")
        self.assertNotIn("hello", json.dumps(self.audit.events[-1]))

    def test_high_sensitivity_requires_one_shot_approval(self) -> None:
        request = self.request(
            capability_id="filesystem.write",
            operation="write_file",
            data_classes=frozenset({"external_write"}),
            arguments={"path": "/tmp/demo.txt", "content": "x"},
        )
        proposal, payload, preview = self.router.propose(request, now=self.now)
        self.assertTrue(proposal.approval_required)
        self.assertTrue(preview.approval_required)
        with self.assertRaises(ToolRoutingError) as missing:
            self.router.execute(proposal, payload, arguments=request.arguments, now=self.now)
        self.assertEqual(missing.exception.code, "TOOL_APPROVAL_UNAVAILABLE")
        self.approvals.approve(proposal, now=self.now)
        result = self.router.execute(
            proposal, payload, arguments=request.arguments, now=self.now,
        )
        self.assertFalse(result.is_error)
        with self.assertRaises(ToolRoutingError) as replay:
            self.router.execute(proposal, payload, arguments=request.arguments, now=self.now)
        self.assertEqual(replay.exception.code, "TOOL_APPROVAL_ALREADY_CONSUMED")

    def test_sandbox_required_blocks_local_installation(self) -> None:
        local_root = Path(self.tempdir.name) / "local-tools"
        local_dir = local_root / "echo"
        local_dir.mkdir(parents=True)
        (local_dir / "mcp-tool.json").write_text(
            json.dumps({
                "schema_version": 1,
                "id": "fixture-echo-mcp",
                "version": "1.0.0",
                "command": "python3",
                "args": ["server.py"],
            }),
            encoding="utf-8",
        )
        registry = ToolRegistry(
            self.product_root,
            catalog_path=TOOL_CATALOG,
            repository_root=ROOT,
            local_paths=[local_root],
        )
        router = ToolRouter(
            registry,
            catalog_path=CATALOG,
            approvals=self.approvals,
            audit=self.audit,
            caller=self.caller,
        )
        request = self.request(
            capability_id="filesystem.write",
            operation="write_file",
            data_classes=frozenset({"external_write"}),
            arguments={"path": "/tmp/demo.txt"},
        )
        proposal, payload, _ = router.propose(request, now=self.now)
        self.approvals.approve(proposal, now=self.now)
        with self.assertRaises(ToolRoutingError) as raised:
            router.execute(proposal, payload, arguments=request.arguments, now=self.now)
        self.assertEqual(raised.exception.code, "TOOL_SANDBOX_REQUIRED")


if __name__ == "__main__":
    unittest.main()
