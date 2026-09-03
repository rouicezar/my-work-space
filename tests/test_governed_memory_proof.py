"""Tests for governed memory integration proof (P7-T05)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from forma_ai.governed_memory_proof import (
    evaluate_proof_payload,
    run_governed_memory_cycle,
    run_governed_memory_proof,
)


class EvaluateProofPayloadTests(unittest.TestCase):
    def test_complete_payload_passes(self) -> None:
        result = evaluate_proof_payload(
            {
                "confirmed_record_id": "rec-1",
                "semantica_id": "sem-1",
                "retrieved": True,
                "conflict_detected": True,
                "corrected_record_id": "rec-2",
                "corrected_version": 2,
                "exported_count": 1,
                "provenance_preserved": True,
                "deleted": True,
                "restarted_retrieve_empty": True,
                "restarted_export_empty": True,
                "history_versions": [1, 2],
            }
        )
        self.assertEqual(result["status"], "proof_passed")

    def test_missing_retrieve_fails(self) -> None:
        result = evaluate_proof_payload(
            {
                "confirmed_record_id": "rec-1",
                "semantica_id": "sem-1",
                "retrieved": False,
                "conflict_detected": True,
                "corrected_record_id": "rec-2",
                "corrected_version": 2,
                "exported_count": 1,
                "provenance_preserved": True,
                "deleted": True,
                "restarted_retrieve_empty": True,
                "restarted_export_empty": True,
                "history_versions": [1, 2],
            }
        )
        self.assertEqual(result["reason"], "retrieve_failed")


@unittest.skipUnless(
    os.environ.get("FORMA_AI_SEMANTICA_INTEGRATION") == "1",
    "pinned Semantica runtime integration is opt-in",
)
class GovernedMemoryIntegrationTests(unittest.TestCase):
    def test_full_workflow_preserves_provenance_and_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "Product"
            payload = run_governed_memory_cycle(root)
            evaluated = evaluate_proof_payload(payload)
            self.assertEqual(evaluated["status"], "proof_passed", msg=json.dumps(payload, indent=2))


class RunGovernedMemoryProofTests(unittest.TestCase):
    def test_uninstalled_environment_fails_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "Product"
            evidence = run_governed_memory_proof(root)
            self.assertEqual(evidence["status"], "proof_failed")
            self.assertEqual(evidence["reason"], "installation_not_verified")

    @unittest.skipUnless(
        os.environ.get("FORMA_AI_SEMANTICA_INTEGRATION") == "1",
        "pinned Semantica runtime integration is opt-in",
    )
    def test_managed_python_worker_proof(self) -> None:
        product_root = os.environ.get("FORMA_AI_PRODUCT_ROOT")
        if not product_root:
            self.skipTest("FORMA_AI_PRODUCT_ROOT is required for managed worker proof")
        root = Path(product_root)
        active = root / "state/components/semantica-active.json"
        if not active.is_file():
            self.skipTest("managed Semantica active record missing")
        with tempfile.TemporaryDirectory() as directory:
            work_root = Path(directory).resolve() / "ProofWork"
            evidence = run_governed_memory_proof(
                root,
                work_root=work_root,
                repository_root=Path(__file__).resolve().parents[1],
            )
        self.assertEqual(evidence["status"], "proof_passed", msg=json.dumps(evidence, indent=2))


if __name__ == "__main__":
    unittest.main()
