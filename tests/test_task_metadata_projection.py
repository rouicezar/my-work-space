"""P8-T01 authority-boundary tests for task metadata projection over Herdr."""

import unittest

from pathlib import Path

from forma_ai.herdr_presentation import HerdrPresentedAgent
from forma_ai.task_metadata_projection import (
    FORBIDDEN_METADATA_CLAIMS,
    RUNTIME_AUTHORITY,
    TaskMetadataProjectionError,
    TaskMetadataRecord,
    binding_contract,
    project_task_view,
    validate_metadata_payload,
    validate_metadata_record,
)


def sample_metadata(**overrides) -> TaskMetadataRecord:
    base = {
        "task_id": "task-1",
        "correlation_id": "corr-1",
        "intent_label": "Summarize release notes",
        "recorded_at": "2026-09-04T00:00:00+00:00",
        "updated_at": "2026-09-04T00:00:00+00:00",
        "run_id": "herdr:task-1:pane-1",
        "herdr_pane_id": "pane-1",
        "herdr_workspace_id": "workspace-1",
        "herdr_tab_id": "tab-1",
        "herdr_terminal_id": "terminal-1",
        "last_accepted_revision": 3,
    }
    base.update(overrides)
    return TaskMetadataRecord(**base)


def sample_agent(**overrides) -> HerdrPresentedAgent:
    base = {
        "pane_id": "pane-1",
        "terminal_id": "terminal-1",
        "workspace_id": "workspace-1",
        "tab_id": "tab-1",
        "state": "working",
        "revision": 4,
    }
    base.update(overrides)
    return HerdrPresentedAgent(**base)


class TaskMetadataProjectionContractTests(unittest.TestCase):
    def test_binding_contract_declares_herdr_authority_and_forbidden_claims(self):
        contract = binding_contract()
        self.assertEqual(contract["runtime_authority"], RUNTIME_AUTHORITY)
        self.assertIn("completed", contract["forbidden_metadata_claims"])
        self.assertIn("task_id", contract["product_owned_fields"])

    def test_metadata_payload_rejects_runtime_completion_or_resumability_claims(self):
        for forbidden in ("completed", "resumable", "runtime_state", "succeeded"):
            with self.subTest(field=forbidden):
                with self.assertRaises(TaskMetadataProjectionError) as raised:
                    validate_metadata_payload({"task_id": "t", forbidden: True})
                self.assertEqual(raised.exception.code, "METADATA_CLAIMS_RUNTIME_AUTHORITY")

    def test_metadata_alone_cannot_project_completion_or_resumability(self):
        metadata = sample_metadata()
        view = project_task_view(metadata, herdr_agent=None, freshness="absent")
        self.assertEqual(view.runtime_state, "unknown")
        self.assertFalse(view.may_resume)
        self.assertFalse(view.is_terminal)
        self.assertEqual(view.display_outcome, "unknown")
        self.assertTrue(view.reconciliation_required)

    def test_stale_herdr_snapshot_fails_closed_even_when_metadata_is_linked(self):
        metadata = sample_metadata()
        agent = sample_agent(state="done", revision=9)
        view = project_task_view(metadata, herdr_agent=agent, freshness="stale")
        self.assertEqual(view.runtime_state, "unknown")
        self.assertFalse(view.may_resume)
        self.assertFalse(view.is_terminal)
        self.assertEqual(view.display_outcome, "unknown")

    def test_fresh_matching_herdr_proof_may_surface_terminal_outcome(self):
        metadata = sample_metadata(last_accepted_revision=8)
        agent = sample_agent(state="done", revision=9)
        view = project_task_view(metadata, herdr_agent=agent, freshness="fresh")
        self.assertEqual(view.runtime_state, "succeeded")
        self.assertTrue(view.is_terminal)
        self.assertEqual(view.display_outcome, "succeeded")
        self.assertFalse(view.may_resume)

    def test_fresh_matching_herdr_proof_may_surface_resumability(self):
        metadata = sample_metadata(last_accepted_revision=4)
        agent = sample_agent(state="blocked", revision=5)
        view = project_task_view(metadata, herdr_agent=agent, freshness="fresh")
        self.assertTrue(view.may_resume)
        self.assertEqual(view.display_outcome, "recoverable")
        self.assertFalse(view.is_terminal)

    def test_revision_or_pane_mismatch_requires_reconciliation(self):
        metadata = sample_metadata(herdr_pane_id="pane-1", last_accepted_revision=10)
        agent = sample_agent(pane_id="pane-2", state="working", revision=11)
        view = project_task_view(metadata, herdr_agent=agent, freshness="fresh")
        self.assertEqual(view.runtime_state, "unknown")
        self.assertTrue(view.reconciliation_required)
        self.assertFalse(view.may_resume)

    def test_swift_contract_file_declares_projection_binding(self):
        swift = (
            Path(__file__).resolve().parents[1]
            / "prototypes/packaging/Sources/LifecycleContract/ProductPreviewProvider.swift"
        ).read_text(encoding="utf-8")
        self.assertIn("TaskMetadataProjectionContract", swift)
        self.assertIn("TaskMetadataPersistenceContract", swift)
        self.assertIn("HistoryRecoveryPreviewContract", swift)


if __name__ == "__main__":
    unittest.main()
