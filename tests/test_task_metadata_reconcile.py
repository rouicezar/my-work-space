"""P8-T03 reconcile tests: stale local metadata fails closed until fresh Herdr proof."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from forma_ai.herdr_adapter import HerdrSessionAgent, HerdrSessionSnapshot
from forma_ai.herdr_presentation import HerdrPresentedAgent
from forma_ai.task_metadata_projection import TaskMetadataRecord
from forma_ai.task_metadata_reconcile import (
    build_herdr_reconcile_snapshot,
    build_reconcile_payload,
    find_linked_agent,
    obtain_herdr_reconcile_snapshot,
    reconcile_task_view,
)
from forma_ai.task_metadata_store import TaskMetadataStore


def sample_record(**overrides) -> TaskMetadataRecord:
    base = {
        "task_id": "task-1",
        "correlation_id": "corr-1",
        "intent_label": "Summarize release notes",
        "recorded_at": "2026-09-04T00:00:00+00:00",
        "updated_at": "2026-09-04T00:00:00+00:00",
        "herdr_pane_id": "pane-1",
        "last_accepted_revision": 3,
    }
    base.update(overrides)
    return TaskMetadataRecord(**base)


def sample_snapshot(**agent_overrides) -> HerdrSessionSnapshot:
    agent = {
        "terminal_id": "terminal-1",
        "agent_status": "done",
        "workspace_id": "workspace-1",
        "tab_id": "tab-1",
        "pane_id": "pane-1",
        "focused": True,
        "revision": 9,
    }
    agent.update(agent_overrides)
    return HerdrSessionSnapshot(
        version="0.8.2",
        protocol=20,
        workspaces=(),
        tabs=(),
        panes=(),
        agents=(HerdrSessionAgent(**agent),),
        layouts=(),
    )


class TaskMetadataReconcileTests(unittest.TestCase):
    def test_stale_herdr_marks_all_tasks_unknown(self):
        metadata = sample_record()
        reconcile = build_herdr_reconcile_snapshot(
            herdr_alive=False,
            snapshot=None,
            reason="HERDR_NOT_RUNNING",
        )
        view = reconcile_task_view(metadata, reconcile)
        self.assertEqual(view.runtime_state, "unknown")
        self.assertEqual(view.display_outcome, "unknown")
        self.assertTrue(view.reconciliation_required)
        self.assertFalse(view.may_resume)

    def test_fresh_matching_snapshot_surfaces_terminal_outcome(self):
        metadata = sample_record(last_accepted_revision=8)
        reconcile = build_herdr_reconcile_snapshot(
            herdr_alive=True,
            snapshot=sample_snapshot(agent_status="done", revision=9),
        )
        view = reconcile_task_view(metadata, reconcile)
        self.assertEqual(view.runtime_state, "succeeded")
        self.assertEqual(view.display_outcome, "succeeded")
        self.assertTrue(view.is_terminal)
        self.assertFalse(view.reconciliation_required)

    def test_missing_pane_in_fresh_snapshot_requires_reconciliation(self):
        metadata = sample_record(herdr_pane_id="pane-missing")
        reconcile = build_herdr_reconcile_snapshot(
            herdr_alive=True,
            snapshot=sample_snapshot(pane_id="pane-other"),
        )
        view = reconcile_task_view(metadata, reconcile)
        self.assertEqual(view.runtime_state, "unknown")
        self.assertTrue(view.reconciliation_required)

    def test_obtain_reconcile_snapshot_fails_closed_when_snapshot_source_errors(self):
        source = Mock()
        source.snapshot.side_effect = RuntimeError("transport down")
        reconcile = obtain_herdr_reconcile_snapshot(
            runtime_status=lambda: {"herdr_alive": True},
            snapshot_source=source,
        )
        self.assertEqual(reconcile.freshness, "stale")
        self.assertEqual(reconcile.reason, "RuntimeError")

    def test_build_payload_reconciles_persisted_tasks_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            TaskMetadataStore(root).save(sample_record())
            source = Mock()
            source.snapshot.return_value = sample_snapshot(agent_status="blocked", revision=5)
            payload = build_reconcile_payload(
                root,
                runtime_status=lambda: {"herdr_alive": True},
                snapshot_source=source,
            )
            self.assertEqual(payload["freshness"], "fresh")
            self.assertEqual(len(payload["tasks"]), 1)
            task = payload["tasks"][0]
            self.assertEqual(task["task_id"], "task-1")
            self.assertEqual(task["display_outcome"], "recoverable")
            self.assertTrue(task["may_resume"])

    def test_build_payload_without_herdr_leaves_tasks_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            TaskMetadataStore(root).save(sample_record())
            payload = build_reconcile_payload(
                root,
                runtime_status=lambda: {"herdr_alive": False},
                snapshot_source=None,
            )
            self.assertEqual(payload["freshness"], "stale")
            self.assertEqual(payload["tasks"][0]["runtime_state"], "unknown")

    def test_find_linked_agent_matches_pane_id(self):
        agent = HerdrPresentedAgent(
            pane_id="pane-1",
            terminal_id="t",
            workspace_id="w",
            tab_id="tab",
            state="working",
            revision=1,
        )
        linked = find_linked_agent(sample_record(), (agent,))
        self.assertIs(linked, agent)


if __name__ == "__main__":
    unittest.main()
