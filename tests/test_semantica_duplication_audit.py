"""Contract tests for the P7-T01 Semantica capability ledger and authority invariants."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from forma_ai.governed_memory import GovernedMemory


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "config/semantica-capability-ledger.json"
ALLOWED_VERDICTS = frozenset({
    "reuse", "inject", "adapter", "upstream_omlx", "product_gap",
    "projection", "product_owned", "preview_only",
})
STORE_CAPABILITIES = frozenset({"memory.store", "memory.get", "memory.forget", "memory.retrieve"})


class SemanticaDuplicationAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_ledger_declares_semantica_as_confirmed_authority(self) -> None:
        self.assertEqual(self.ledger["schema_version"], 1)
        self.assertEqual(self.ledger["confirmed_authority"], "semantica")
        self.assertEqual(self.ledger["pinned_upstream"]["semantica"]["version"], "0.6.7")

    def test_storage_and_retrieval_capabilities_remain_upstream_bound(self) -> None:
        by_id = {item["id"]: item for item in self.ledger["capabilities"]}
        for capability_id in STORE_CAPABILITIES:
            row = by_id[capability_id]
            self.assertEqual(row["authority"], "semantica")
            self.assertIn(row["verdict"], {"reuse", "inject", "adapter"})
            self.assertIsNotNone(row["upstream_entry"])

    def test_no_confirmed_authority_competes_with_semantica(self) -> None:
        for row in self.ledger["capabilities"]:
            self.assertIn(row["verdict"], ALLOWED_VERDICTS)
            if row["verdict"] in {"reuse", "inject", "adapter", "projection"}:
                self.assertEqual(row["authority"], "semantica")
            if row["verdict"] == "projection":
                self.assertNotEqual(row["p7_t02_action"], "none")

    def test_governed_memory_health_reports_semantica_authority(self) -> None:
        class HealthyBackend:
            def health(self) -> dict[str, str]:
                return {"status": "healthy"}

            def store(self, content: str, metadata: dict) -> str:
                return "sem-1"

            def get(self, memory_id: str):
                return None

            def retrieve(self, query: str, limit: int):
                return []

            def forget(self, memory_id: str) -> bool:
                return False

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            health = GovernedMemory(root, HealthyBackend()).health()
        self.assertEqual(health["confirmed_authority"], "semantica")

    def test_audit_document_and_binding_decision_exist(self) -> None:
        audit = ROOT / "docs/research/p7-t01-semantica-duplication-audit-2026-09-03.md"
        binding = ROOT / "docs/research/semantica-binding-decision-2026-09-03.md"
        self.assertTrue(audit.is_file(), "P7-T01 audit document must exist")
        self.assertTrue(binding.is_file(), "F1/F4 binding decision must exist")


if __name__ == "__main__":
    unittest.main()
