import tempfile
import unittest
from pathlib import Path

from forma_ai.lifecycle import LifecycleError, LifecycleJournal


class LifecycleJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.journal = LifecycleJournal(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_install_is_resumable_and_idempotent(self):
        begun = self.journal.begin("install", ["preflight", "configure", "verify"])
        same = self.journal.begin("install", ["preflight", "configure", "verify"])
        self.assertEqual(begun.operation_id, same.operation_id)

        self.assertEqual(self.journal.start_next().active_step, "preflight")
        self.journal.complete_active()
        self.assertEqual(self.journal.start_next().active_step, "configure")

        reloaded = LifecycleJournal(Path(self.temp.name))
        self.assertEqual(reloaded.start_next().active_step, "configure")
        reloaded.complete_active()
        self.assertEqual(reloaded.start_next().active_step, "verify")
        final = reloaded.complete_active()
        self.assertEqual(final.phase, "completed")
        self.assertEqual(final.completed_steps, ["preflight", "configure", "verify"])

    def test_failure_is_honest_and_resumes_same_step(self):
        self.journal.begin("install", ["download", "verify"])
        self.journal.start_next()
        failed = self.journal.fail_active("NETWORK", "download interrupted")
        self.assertEqual(failed.phase, "failed")
        self.assertEqual(failed.error["step"], "download")

        resumed = self.journal.resume_failed()
        self.assertEqual(resumed.phase, "running")
        self.assertEqual(resumed.active_step, "download")
        self.assertIsNone(resumed.error)

    def test_new_operation_cannot_replace_active_operation(self):
        self.journal.begin("install", ["preflight"])
        with self.assertRaisesRegex(LifecycleError, "still active"):
            self.journal.begin("repair", ["diagnose"])

    def test_uninstall_requires_explicit_data_policy(self):
        with self.assertRaisesRegex(LifecycleError, "data policy"):
            self.journal.begin("uninstall", ["stop", "remove"])
        state = self.journal.begin("uninstall", ["stop", "remove"], data_policy="keep")
        self.assertEqual(state.data_policy, "keep")

    def test_event_log_is_ordered_and_correlated(self):
        state = self.journal.begin("repair", ["diagnose"])
        self.journal.start_next()
        self.journal.complete_active()
        events = self.journal.events()
        self.assertEqual([item["sequence"] for item in events], list(range(1, len(events) + 1)))
        self.assertEqual({item["operation_id"] for item in events}, {state.operation_id})
        self.assertEqual(events[-1]["event"], "operation_completed")


if __name__ == "__main__":
    unittest.main()
