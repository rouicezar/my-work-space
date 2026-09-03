"""P8-T02 persistence tests for product task metadata without runtime claims."""

import json
import tempfile
import unittest
from pathlib import Path

from forma_ai.task_metadata_projection import (
    TaskMetadataProjectionError,
    TaskMetadataRecord,
    project_task_view,
    validate_metadata_payload,
)
from forma_ai.task_metadata_store import TaskMetadataStore, TaskMetadataStoreError, binding_contract


def sample_record(**overrides) -> TaskMetadataRecord:
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
        "approval_refs": ("approval:cloud:abc",),
        "artifact_refs": ("artifact:report:xyz",),
        "policy_preview_digest": "sha256:deadbeef",
    }
    base.update(overrides)
    return TaskMetadataRecord(**base)


class TaskMetadataStoreTests(unittest.TestCase):
    def test_binding_contract_declares_no_runtime_claim_persistence(self):
        contract = binding_contract()
        self.assertFalse(contract["persists_runtime_claims"])
        self.assertEqual(contract["storage_relative_directory"], "state/task-metadata")

    def test_save_and_restart_reload_product_owned_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            record = sample_record()
            TaskMetadataStore(root).save(record)
            reloaded = TaskMetadataStore(root).load("task-1")
            self.assertEqual(reloaded.task_id, record.task_id)
            self.assertEqual(reloaded.correlation_id, record.correlation_id)
            self.assertEqual(reloaded.intent_label, record.intent_label)
            self.assertEqual(reloaded.last_accepted_revision, 3)
            self.assertEqual(reloaded.approval_refs, ("approval:cloud:abc",))
            self.assertEqual(reloaded.artifact_refs, ("artifact:report:xyz",))
            self.assertEqual(TaskMetadataStore(root).list_task_ids(), ("task-1",))

    def test_update_preserves_directory_permissions_and_overwrites_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            store = TaskMetadataStore(root)
            store.save(sample_record(last_accepted_revision=1))
            updated = sample_record(
                last_accepted_revision=5,
                updated_at="2026-09-04T01:00:00+00:00",
                approval_refs=("approval:tool:def",),
            )
            store.save(updated)
            reloaded = TaskMetadataStore(root).load("task-1")
            self.assertEqual(reloaded.last_accepted_revision, 5)
            self.assertEqual(reloaded.approval_refs, ("approval:tool:def",))
            self.assertEqual(store.directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual(store._path("task-1").stat().st_mode & 0o777, 0o600)

    def test_persisted_metadata_cannot_project_completion_without_herdr(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            record = TaskMetadataStore(root).save(sample_record(last_accepted_revision=99))
            view = project_task_view(record, herdr_agent=None, freshness="absent")
            self.assertEqual(view.runtime_state, "unknown")
            self.assertFalse(view.is_terminal)
            self.assertFalse(view.may_resume)
            self.assertEqual(view.display_outcome, "unknown")

    def test_save_rejects_forbidden_runtime_claim_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            store = TaskMetadataStore(root)
            store.save(sample_record())
            path = store._path("task-1")
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["completed"] = True
            path.write_text(json.dumps(raw))
            with self.assertRaises(TaskMetadataStoreError) as raised:
                store.load("task-1")
            self.assertEqual(raised.exception.code, "METADATA_INVALID")

    def test_corrupt_world_readable_and_symlink_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory) / "Product"
            store = TaskMetadataStore(root)
            store.save(sample_record())
            store._path("task-1").chmod(0o644)
            with self.assertRaises(TaskMetadataStoreError) as raised:
                store.load("task-1")
            self.assertEqual(raised.exception.code, "METADATA_UNSAFE")

            target = Path(outside) / "task-1.json"
            target.write_text("{}")
            store._path("task-1").unlink()
            store._path("task-1").symlink_to(target)
            with self.assertRaises(TaskMetadataStoreError) as raised:
                store.load("task-1")
            self.assertEqual(raised.exception.code, "METADATA_UNSAFE")

    def test_validate_metadata_payload_blocks_runtime_claims_before_persist(self):
        with self.assertRaises(TaskMetadataProjectionError):
            validate_metadata_payload({"task_id": "t", "resumable": True})


if __name__ == "__main__":
    unittest.main()
