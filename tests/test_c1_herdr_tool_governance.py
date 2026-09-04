"""C1-T03 red contracts for the Herdr Agent tool-governance boundary."""

from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from forma_ai.herdr_tool_bridge import HerdrToolBridge
from forma_ai.tool_registry import ToolRegistry
from forma_ai.tool_routing import ToolApprovalStore


ROOT = Path(__file__).resolve().parents[1]


class HerdrToolGovernanceRedTests(unittest.TestCase):
    def test_sensitive_agent_tool_call_never_manufactures_its_own_approval(self):
        """The Agent-facing bridge may propose or execute, but cannot approve."""
        with tempfile.TemporaryDirectory() as directory:
            product_root = Path(directory) / "Product"
            product_root.mkdir()
            ToolRegistry(
                product_root,
                catalog_path=ROOT / "config/tool-packages.json",
                repository_root=ROOT,
            ).install("fixture-echo-mcp")

            with patch.object(
                ToolApprovalStore,
                "approve",
                autospec=True,
            ) as approve:
                artifact = HerdrToolBridge(repository_root=ROOT).call(
                    product_root=product_root,
                    correlation_id=str(uuid.uuid4()),
                    capability_id="filesystem.write",
                    operation="write_file",
                    arguments={"path": "/tmp/forbidden.txt", "content": "x"},
                    data_classes=frozenset({"external_write"}),
                    catalog_path=ROOT / "config/tool-routing.json",
                )

            approve.assert_not_called()
            self.assertTrue(artifact.is_error)
            self.assertIn("TOOL_APPROVAL_REQUIRED", artifact.text)
            proposal_id = artifact.text.split(":", 1)[1]
            proposal_dir = product_root / "state" / "tool-proposals"
            self.assertTrue((proposal_dir / f"{proposal_id}.json").is_file())
            self.assertTrue((proposal_dir / f"{proposal_id}.payload").is_file())


if __name__ == "__main__":
    unittest.main()
