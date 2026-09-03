"""P8-T04 recovery route tests with revision-checked Herdr lifecycle binding."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from forma_ai.herdr_adapter import HerdrLifecycleResult, HerdrSessionAgent, HerdrSessionSnapshot, HerdrTask
from forma_ai.herdr_presentation import HerdrPresentedAgent
from forma_ai.task_history_recovery import (
    TaskHistoryRecoveryError,
    RecoveryContext,
    binding_contract,
    execute_cancel,
    execute_reclaim,
    load_recovery_context,
    validate_cancel_eligibility,
)
from forma_ai.task_metadata_projection import TaskMetadataRecord
from forma_ai.task_metadata_reconcile import build_herdr_reconcile_snapshot, reconcile_task_view
from forma_ai.task_metadata_store import TaskMetadataStore


def sample_record(**overrides) -> TaskMetadataRecord:
    base = {
        "task_id": "task-1",
        "correlation_id": "corr-1",
        "intent_label": "Summarize release notes",
        "recorded_at": "2026-09-04T00:00:00+00:00",
        "updated_at": "2026-09-04T00:00:00+00:00",
        "run_id": "run-1",
        "herdr_pane_id": "pane-1",
        "last_accepted_revision": 4,
    }
    base.update(overrides)
    return TaskMetadataRecord(**base)


def sample_agent(**overrides) -> HerdrPresentedAgent:
    base = {
        "pane_id": "pane-1",
        "terminal_id": "terminal-1",
        "workspace_id": "workspace-1",
        "tab_id": "tab-1",
        "state": "blocked",
        "revision": 5,
    }
    base.update(overrides)
    return HerdrPresentedAgent(**base)


def sample_snapshot(**agent_overrides) -> HerdrSessionSnapshot:
    agent = {
        "terminal_id": "terminal-1",
        "agent_status": "blocked",
        "workspace_id": "workspace-1",
        "tab_id": "tab-1",
        "pane_id": "pane-1",
        "focused": True,
        "revision": 5,
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


class TaskHistoryRecoveryTests(unittest.TestCase):
    def test_binding_contract_declares_supervisor_recovery_routes(self):
        contract = binding_contract()
        self.assertEqual(contract["recovery_actions"]["cancel"], "task-history-cancel")
        self.assertTrue(contract["requires_matching_revision"])

    def test_cancel_rejects_revision_mismatch(self):
        metadata = sample_record()
        reconcile = build_herdr_reconcile_snapshot(herdr_alive=True, snapshot=sample_snapshot())
        view = reconcile_task_view(metadata, reconcile)
        context = RecoveryContext(metadata=metadata, view=view, agent=sample_agent())
        with self.assertRaises(TaskHistoryRecoveryError) as raised:
            validate_cancel_eligibility(context, expected_revision=4)
        self.assertEqual(raised.exception.code, "RECOVERY_REVISION_MISMATCH")

    def test_execute_reclaim_delegates_to_herdr_adapter(self):
        metadata = sample_record()
        reconcile = build_herdr_reconcile_snapshot(herdr_alive=True, snapshot=sample_snapshot())
        view = reconcile_task_view(metadata, reconcile)
        context = RecoveryContext(metadata=metadata, view=view, agent=sample_agent())
        adapter = Mock()
        adapter.reclaim_task.return_value = HerdrTask(
            task_id="task-1", run_id="run-1", workspace_id="workspace-1",
            pane_id="pane-1", terminal_id="terminal-1", state="blocked", revision=5,
        )
        result = execute_reclaim(context, adapter)
        self.assertEqual(result["action"], "reclaim")
        adapter.reclaim_task.assert_called_once()

    def test_execute_cancel_requires_matching_revision(self):
        metadata = sample_record()
        reconcile = build_herdr_reconcile_snapshot(
            herdr_alive=True,
            snapshot=sample_snapshot(agent_status="working"),
        )
        view = reconcile_task_view(metadata, reconcile)
        context = RecoveryContext(
            metadata=metadata,
            view=view,
            agent=sample_agent(state="working"),
        )
        adapter = Mock()
        adapter.reclaim_task.return_value = HerdrTask(
            task_id="task-1", run_id="run-1", workspace_id="workspace-1",
            pane_id="pane-1", terminal_id="terminal-1", state="running", revision=5,
        )
        adapter.cancel_task.return_value = HerdrLifecycleResult(
            task_id="task-1", run_id="run-1", action="graceful_interrupt",
            state="cancel_requested", revision=5,
        )
        result = execute_cancel(context, adapter, expected_revision=5, correlation_id="corr-2")
        self.assertEqual(result["action"], "graceful_interrupt")

    def test_load_recovery_context_fails_when_agent_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            TaskMetadataStore(root).save(sample_record(herdr_pane_id="pane-missing"))
            with self.assertRaises(TaskHistoryRecoveryError) as raised:
                load_recovery_context(
                    root,
                    "task-1",
                    runtime_status=lambda: {"herdr_alive": True},
                    snapshot_source=Mock(snapshot=Mock(return_value=HerdrSessionSnapshot(
                        version="0.8.2", protocol=20, workspaces=(), tabs=(), panes=(), agents=(), layouts=(),
                    ))),
                )
            self.assertEqual(raised.exception.code, "RECOVERY_AGENT_MISSING")


if __name__ == "__main__":
    unittest.main()
