"""P8-T05 rediscovery proof tests for app reopen and Herdr detach/reconnect."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from forma_ai.herdr_adapter import HerdrTask
from forma_ai.task_history_rediscovery import (
    TaskHistoryRediscoveryError,
    binding_contract,
    evaluate_rediscovery_proof,
    list_rediscovered_task_ids,
    multi_agent_snapshot,
    observe_rediscovery,
    run_rediscovery_proof,
)
from forma_ai.task_metadata_projection import TaskMetadataRecord


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


class TaskHistoryRediscoveryTests(unittest.TestCase):
    def test_binding_contract_declares_proof_phases(self):
        contract = binding_contract()
        self.assertIn("app_reopened", contract["proof_phases"])
        self.assertTrue(contract["false_completion_forbidden"])

    def test_rediscovered_tasks_survive_app_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            from forma_ai.task_metadata_store import TaskMetadataStore

            TaskMetadataStore(root).save(sample_record())
            TaskMetadataStore(root).save(sample_record(
                task_id="task-2",
                correlation_id="corr-2",
                run_id="run-2",
                herdr_pane_id="pane-2",
            ))
            self.assertEqual(
                list_rediscovered_task_ids(root),
                ("task-1", "task-2"),
            )

    def test_herdr_detach_fails_closed_without_false_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            from forma_ai.task_metadata_store import TaskMetadataStore

            TaskMetadataStore(root).save(sample_record(last_accepted_revision=99))
            observation = observe_rediscovery(
                root,
                phase="herdr_detached",
                runtime_status=lambda: {"herdr_alive": False},
                snapshot_source=None,
            )
            self.assertEqual(len(observation.tasks), 1)
            task = observation.tasks[0]
            self.assertEqual(task["runtime_state"], "unknown")
            self.assertFalse(task["is_terminal"])

    def test_run_rediscovery_proof_passes_reopen_detach_reconnect_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            snapshot_source = Mock()
            snapshot_source.snapshot.return_value = multi_agent_snapshot(
                {
                    "terminal_id": "terminal-1",
                    "agent_status": "done",
                    "workspace_id": "workspace-1",
                    "tab_id": "tab-1",
                    "pane_id": "pane-1",
                    "focused": True,
                    "revision": 9,
                },
                {
                    "terminal_id": "terminal-2",
                    "agent_status": "blocked",
                    "workspace_id": "workspace-1",
                    "tab_id": "tab-1",
                    "pane_id": "pane-2",
                    "focused": False,
                    "revision": 5,
                },
            )
            adapter = Mock()
            adapter.reclaim_task.return_value = HerdrTask(
                task_id="task-2", run_id="run-2", workspace_id="workspace-1",
                pane_id="pane-2", terminal_id="terminal-2", state="blocked", revision=5,
            )
            result = run_rediscovery_proof(
                root,
                records=(
                    sample_record(last_accepted_revision=8),
                    sample_record(
                        task_id="task-2",
                        correlation_id="corr-2",
                        run_id="run-2",
                        herdr_pane_id="pane-2",
                        last_accepted_revision=4,
                    ),
                ),
                detached_status=lambda: {"herdr_alive": False},
                reconnected_status=lambda: {"herdr_alive": True},
                reconnected_snapshot_source=snapshot_source,
                reclaim_adapter=adapter,
            )
            self.assertEqual(result["status"], "proof_passed")
            self.assertEqual(result["rediscovered_task_ids"], ["task-1", "task-2"])
            self.assertTrue(result["detached_all_unknown"])
            self.assertTrue(result["recoverable_after_reconnect"])
            self.assertTrue(result["reclaim_after_reopen"])
            self.assertTrue(result["terminal_with_fresh_herdr_proof"])

    def test_evaluate_rediscovery_proof_fails_when_detach_not_unknown(self):
        result = evaluate_rediscovery_proof({
            "rediscovered_task_ids": ["task-1"],
            "detached_all_unknown": False,
            "reconnected_without_false_completion": True,
            "recoverable_after_reconnect": True,
            "reclaim_after_reopen": True,
        })
        self.assertEqual(result["status"], "proof_failed")
        self.assertEqual(result["reason"], "detach_did_not_fail_closed")

    def test_run_rediscovery_proof_raises_when_tasks_not_rediscovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            with self.assertRaises(TaskHistoryRediscoveryError) as raised:
                run_rediscovery_proof(
                    root,
                    records=(),
                    detached_status=lambda: {"herdr_alive": False},
                    reconnected_status=lambda: {"herdr_alive": True},
                    reconnected_snapshot_source=Mock(),
                    reclaim_adapter=Mock(),
                )
            self.assertEqual(raised.exception.code, "REDISCOVERY_EMPTY")


if __name__ == "__main__":
    unittest.main()
