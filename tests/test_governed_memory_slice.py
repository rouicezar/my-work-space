"""P7-T07 governed-memory slice closeout contract tests."""

import json
import unittest
from pathlib import Path

from forma_ai.memory_review_binding import (
    CONFIRMED_AUTHORITY,
    MEMORY_REVIEW_AUDIT_PATH,
    SUPERVISOR_COMMANDS,
    binding_contract,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class GovernedMemorySliceCloseoutTests(unittest.TestCase):
    def test_binding_contract_matches_supervisor_and_swift_surface(self):
        contract = binding_contract()
        self.assertEqual(contract["confirmed_authority"], CONFIRMED_AUTHORITY)
        self.assertEqual(contract["supervisor_commands"], SUPERVISOR_COMMANDS)
        swift = (
            REPOSITORY_ROOT
            / "prototypes/packaging/Sources/LifecycleContract/ProductPreviewProvider.swift"
        ).read_text(encoding="utf-8")
        self.assertIn("memory-review-snapshot", swift)
        self.assertIn("GovernedMemoryReviewPanel", (
            REPOSITORY_ROOT / "prototypes/packaging/Sources/FormaAIApp/GovernedMemoryReviewPanel.swift"
        ).read_text(encoding="utf-8"))
        self.assertIn(MEMORY_REVIEW_AUDIT_PATH, swift)

    def test_ledger_records_preview_and_runtime_binding_without_second_authority(self):
        ledger = json.loads(
            (REPOSITORY_ROOT / "config/semantica-capability-ledger.json").read_text(encoding="utf-8")
        )
        self.assertEqual(ledger["confirmed_authority"], "semantica")
        preview = next(item for item in ledger["capabilities"] if item["id"] == "memory.preview_ui")
        self.assertEqual(preview.get("p7_t06_action"), "completed")
        self.assertNotIn("competing", json.dumps(ledger).lower())

    def test_p7_t07_evidence_document_exists(self):
        evidence = REPOSITORY_ROOT / "evidence/memory/p7-t07-governed-memory-slice-closeout-2026-09-04.md"
        self.assertTrue(evidence.is_file(), "P7-T07 evidence must exist before closeout")


if __name__ == "__main__":
    unittest.main()
