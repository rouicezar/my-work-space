import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from forma_ai.cloud_catalog import load_cloud_provider
from forma_ai.cloud_preferences import CloudPreferenceStore


ROOT = Path(__file__).resolve().parents[1]


class CloudPreferenceStoreTests(unittest.TestCase):
    def setUp(self):
        self.provider = load_cloud_provider(ROOT / "config/cloud-providers.json", "deepseek")
        self.now = datetime(2026, 8, 30, 12, tzinfo=timezone.utc)

    def test_missing_state_is_disabled_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            state = CloudPreferenceStore(root).load(self.provider)
            self.assertFalse(state.enabled)
            self.assertTrue(state.valid)
            self.assertEqual(state.code, "CLOUD_DISABLED_DEFAULT")
            self.assertFalse(root.exists())

    def test_enable_disable_and_restart_persist_private_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            store = CloudPreferenceStore(root)
            enabled = store.save(
                enabled=True, provider=self.provider, model_id="deepseek-v4-flash", now=self.now,
            )
            self.assertTrue(enabled.enabled)
            self.assertEqual(CloudPreferenceStore(root).load(self.provider).model_id, "deepseek-v4-flash")
            self.assertEqual(store.directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual(store.path.stat().st_mode & 0o777, 0o600)
            store.save(enabled=False, now=self.now)
            self.assertFalse(CloudPreferenceStore(root).load(self.provider).enabled)

    def test_corrupt_world_readable_and_unknown_model_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            store = CloudPreferenceStore(root)
            store.save(enabled=True, provider=self.provider, model_id="deepseek-v4-flash", now=self.now)
            raw = json.loads(store.path.read_text())
            raw["model_id"] = "unknown"
            store.path.write_text(json.dumps(raw))
            self.assertEqual(store.load(self.provider).code, "CLOUD_PREFERENCES_INVALID")
            store.path.chmod(0o644)
            self.assertEqual(store.load(self.provider).code, "CLOUD_PREFERENCES_UNSAFE")

    def test_symlink_state_fails_closed_without_following(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory) / "Product"
            path = root / "config/cloud-preferences.json"
            path.parent.mkdir(parents=True)
            target = Path(outside) / "target.json"
            target.write_text("{}")
            path.symlink_to(target)
            state = CloudPreferenceStore(root).load(self.provider)
            self.assertFalse(state.enabled)
            self.assertEqual(state.code, "CLOUD_PREFERENCES_UNSAFE")


if __name__ == "__main__":
    unittest.main()
