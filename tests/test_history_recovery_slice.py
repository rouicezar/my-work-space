"""P8-T07 history/cancel/resume projection slice closeout contract tests."""

import json
import subprocess
import unittest
from pathlib import Path

from forma_ai.task_history_binding import (
    SUPERVISOR_COMMANDS,
    TASK_HISTORY_AUDIT_PATH,
    TASK_HISTORY_RECOVERY_AUDIT_PATH,
)
from forma_ai.task_history_recovery import binding_contract as recovery_binding_contract
from forma_ai.task_metadata_projection import FORBIDDEN_METADATA_CLAIMS


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
P8_SLICE_COMMITS = (
    "28ebfee",  # P8-T01
    "54e2149",  # P8-T02
    "5f15bbb",  # P8-T03
    "47a0af2",  # P8-T04
    "28e84c0",  # P8-T05
    "231ed4d",  # P8-T06
)


class HistoryRecoverySliceCloseoutTests(unittest.TestCase):
    def test_recovery_binding_matches_supervisor_and_swift_surface(self):
        contract = recovery_binding_contract()
        self.assertEqual(contract["runtime_authority"], "herdr")
        self.assertEqual(contract["recovery_actions"]["reclaim"], SUPERVISOR_COMMANDS["reclaim"])
        self.assertEqual(contract["recovery_actions"]["cancel"], SUPERVISOR_COMMANDS["cancel"])
        self.assertEqual(contract["recovery_actions"]["fresh_run"], SUPERVISOR_COMMANDS["fresh_run"])
        self.assertTrue(contract["requires_fresh_reconcile"])
        self.assertTrue(contract["requires_matching_revision"])

        swift = (
            REPOSITORY_ROOT
            / "prototypes/packaging/Sources/LifecycleContract/ProductPreviewProvider.swift"
        ).read_text(encoding="utf-8")
        panel = (
            REPOSITORY_ROOT / "prototypes/packaging/Sources/FormaAIApp/HistoryRecoveryPanel.swift"
        ).read_text(encoding="utf-8")

        self.assertIn("task-metadata-reconcile", swift)
        self.assertIn("task-history-reclaim", swift)
        self.assertIn(TASK_HISTORY_AUDIT_PATH, swift)
        self.assertIn(TASK_HISTORY_RECOVERY_AUDIT_PATH, swift)
        self.assertIn("HistoryRecoveryServiceBinding", swift)
        self.assertIn("readsPersistedHistory: false", swift)
        self.assertIn("HistoryRecoveryPanel", panel)
        self.assertIn("taskMetadataReconcile", panel)

    def test_ledger_records_herdr_authority_without_competing_state_machine(self):
        ledger = json.loads(
            (REPOSITORY_ROOT / "config/herdr-history-capability-ledger.json").read_text(encoding="utf-8")
        )
        self.assertEqual(ledger["confirmed_authority"], "herdr")
        self.assertEqual(ledger["task_id"], "P8-T07")
        preview = next(item for item in ledger["capabilities"] if item["id"] == "history.preview_ui")
        runtime = next(item for item in ledger["capabilities"] if item["id"] == "history.runtime_panel")
        self.assertEqual(preview.get("p8_t07_action"), "runtime_panel_wired_no_second_state_machine")
        self.assertEqual(runtime.get("p8_t07_action"), "wired_requires_runtime")
        self.assertNotIn("competing", json.dumps(ledger).lower())

    def test_metadata_projection_forbids_runtime_claims_in_storage(self):
        store = (REPOSITORY_ROOT / "forma_ai/task_metadata_store.py").read_text(encoding="utf-8")
        self.assertNotIn("may_resume", store)
        self.assertNotIn("runtime_state", store)
        self.assertIn("state/task-metadata", store)
        self.assertIn("completed", FORBIDDEN_METADATA_CLAIMS)
        self.assertIn("resumable", FORBIDDEN_METADATA_CLAIMS)

    def test_p8_slice_commits_exist_on_main(self):
        for commit in P8_SLICE_COMMITS:
            result = subprocess.run(
                ["git", "cat-file", "-t", commit],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"missing P8 slice commit {commit}")
            self.assertEqual(result.stdout.strip(), "commit")

    def test_p8_t07_evidence_document_exists(self):
        evidence = REPOSITORY_ROOT / "evidence/recovery/p8-t07-history-recovery-slice-closeout-2026-09-04.md"
        self.assertTrue(evidence.is_file(), "P8-T07 evidence must exist before closeout")


if __name__ == "__main__":
    unittest.main()
