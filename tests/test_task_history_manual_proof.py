"""P8-T06 manual recovery evidence tests."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from forma_ai.herdr_adapter import HerdrTask
from forma_ai.task_history_manual_proof import (
    binding_contract,
    build_recovery_evidence_payload,
    evaluate_recovery_evidence,
    interrupted_task_record,
    render_recovery_evidence_markdown,
    run_automated_recovery_proof,
)
from forma_ai.task_history_rediscovery import multi_agent_snapshot
from forma_ai.task_metadata_store import TaskMetadataStore


class TaskHistoryManualProofTests(unittest.TestCase):
    def test_binding_contract_declares_manual_checklist(self):
        contract = binding_contract()
        self.assertEqual(contract["scenario_id"], "interrupted_blocked_task")
        self.assertIn("reclaim", contract["supervisor_commands"])

    def test_automated_interrupted_recovery_proof_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            snapshot_source = Mock()
            snapshot_source.snapshot.return_value = multi_agent_snapshot(
                {
                    "terminal_id": "terminal-interrupted-1",
                    "agent_status": "blocked",
                    "workspace_id": "workspace-1",
                    "tab_id": "tab-1",
                    "pane_id": "pane-interrupted-1",
                    "focused": True,
                    "revision": 7,
                },
            )
            adapter = Mock()
            adapter.reclaim_task.return_value = HerdrTask(
                task_id="task-interrupted-1",
                run_id="run-interrupted-1",
                workspace_id="workspace-1",
                pane_id="pane-interrupted-1",
                terminal_id="terminal-interrupted-1",
                state="blocked",
                revision=7,
            )
            result = run_automated_recovery_proof(
                root,
                detached_status=lambda: {"herdr_alive": False},
                reconnected_status=lambda: {"herdr_alive": True},
                reconnected_snapshot_source=snapshot_source,
                reclaim_adapter=adapter,
            )
            self.assertEqual(result["status"], "automated_proof_passed")
            self.assertTrue(result["detached_unknown"])
            self.assertTrue(result["reconnected_may_resume"])
            self.assertTrue(result["reclaim_after_reopen"])

    def test_recovery_evidence_records_manual_signoff_pending(self):
        payload = {
            "automated": {
                "status": "automated_proof_passed",
                "rediscovered_task_ids": ["task-interrupted-1"],
                "detached_unknown": True,
                "reconnected_may_resume": True,
                "reclaim_after_reopen": True,
            },
            "manual_checklist": {
                "native_history_lists_persisted_task_after_reopen": False,
            },
        }
        evaluation = evaluate_recovery_evidence(payload)
        self.assertEqual(evaluation["status"], "proof_recorded")
        self.assertTrue(evaluation["manual_signoff_required"])

    def test_render_recovery_evidence_markdown_includes_checklist(self):
        markdown = render_recovery_evidence_markdown(
            {
                "automated": {
                    "status": "automated_proof_passed",
                    "rediscovered_task_ids": ["task-interrupted-1"],
                    "detached_unknown": True,
                    "reconnected_may_resume": True,
                    "reclaim_after_reopen": True,
                },
                "manual_checklist": {},
                "evaluation": {"status": "proof_recorded"},
            },
            proof_date="2026-09-04",
        )
        self.assertIn("Recovery Proof — 2026-09-04", markdown)
        self.assertIn("native_history_lists_persisted_task_after_reopen", markdown)

    def test_build_payload_persists_interrupted_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            record = interrupted_task_record()
            TaskMetadataStore(root).save(record)
            snapshot_source = Mock()
            snapshot_source.snapshot.return_value = multi_agent_snapshot(
                {
                    "terminal_id": "terminal-interrupted-1",
                    "agent_status": "blocked",
                    "workspace_id": "workspace-1",
                    "tab_id": "tab-1",
                    "pane_id": "pane-interrupted-1",
                    "focused": True,
                    "revision": 7,
                },
            )
            adapter = Mock()
            adapter.reclaim_task.return_value = HerdrTask(
                task_id=record.task_id,
                run_id=record.run_id,
                workspace_id="workspace-1",
                pane_id=record.herdr_pane_id,
                terminal_id=record.herdr_terminal_id,
                state="blocked",
                revision=7,
            )
            payload = build_recovery_evidence_payload(
                root,
                detached_status=lambda: {"herdr_alive": False},
                reconnected_status=lambda: {"herdr_alive": True},
                reconnected_snapshot_source=snapshot_source,
                reclaim_adapter=adapter,
            )
            self.assertEqual(payload["evaluation"]["status"], "proof_recorded")


if __name__ == "__main__":
    unittest.main()
