"""P6-T07 proof: governed workbook merge + HTML report with audit evidence."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from forma_ai.tool_e2e_runner import ToolE2ERunner


ROOT = Path(__file__).resolve().parents[1]


class ToolE2EProofTests(unittest.TestCase):
    PROOF_ID = "P6-T07"

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="forma-p6t07-test-")
        self.product_root = Path(self.tempdir.name) / "Product"
        self.product_root.mkdir()
        self.workspace = Path(self.tempdir.name) / "workspace"
        self.workspace.mkdir()
        self.correlation_id = str(uuid.uuid4())

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_workbook_merge_and_report_with_audit(self) -> None:
        result = ToolE2ERunner().run_workbook_report(
            product_root=self.product_root,
            workspace_dir=self.workspace,
            correlation_id=self.correlation_id,
            repository_root=ROOT,
        )

        self.assertTrue(result.sheet_a_path.is_file())
        self.assertTrue(result.sheet_b_path.is_file())
        self.assertTrue(result.merged_csv_path.is_file())
        self.assertTrue(result.report_html_path.is_file())

        with result.merged_csv_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(rows[0], ["name", "amount"])
        self.assertEqual(len(rows) - 1, 3)
        names = {row[0] for row in rows[1:]}
        self.assertEqual(names, {"Alice", "Bob", "Carol"})

        report = result.report_html_path.read_text(encoding="utf-8")
        self.assertIn("<table>", report)
        self.assertIn("Alice", report)
        self.assertIn("Carol", report)

        self.assertTrue(result.audit_log_path.is_file())
        events = [
            json.loads(line)
            for line in result.audit_log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        event_names = {item["event"] for item in events}
        self.assertIn("tool_route_proposed", event_names)
        self.assertIn("tool_call", event_names)
        tool_calls = [item for item in events if item.get("event") == "tool_call"]
        self.assertGreaterEqual(len(tool_calls), 2)
        self.assertTrue(all(item.get("outcome") == "completed" for item in tool_calls))
        self.assertEqual(result.correlation_id, self.correlation_id)


if __name__ == "__main__":
    unittest.main()
