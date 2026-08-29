import tempfile
import unittest
from pathlib import Path

from mac_ai_work_os.processes import ProcessPolicyError, omlx_process_spec


class OMLXProcessSpecTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.gettempdir()) / "MacAIWorkOSTest"
        self.executable = Path("/Applications/oMLX.app/Contents/MacOS/omlx-cli")

    def test_spec_isolates_home_data_models_cache_and_temp(self):
        cache = self.root / "Caches"
        spec = omlx_process_spec(
            executable=self.executable, app_support=self.root, cache_root=cache
        )
        data = self.root / "data" / "omlx"
        self.assertEqual(spec.environment["HOME"], str(self.root / "state" / "homes" / "omlx"))
        self.assertEqual(spec.environment["XDG_CACHE_HOME"], str(cache / "omlx" / "xdg"))
        self.assertEqual(spec.environment["HF_HOME"], str(cache / "omlx" / "huggingface"))
        self.assertEqual(spec.environment["TMPDIR"], str(self.root / "state" / "runtime" / "omlx" / "tmp"))
        self.assertEqual(spec.environment["PATH"], "/usr/bin:/bin:/usr/sbin:/sbin")
        self.assertFalse(spec.inherit_parent_environment)
        self.assertIn(str(data), spec.arguments)
        self.assertIn(str(data / "models"), spec.arguments)

    def test_spec_is_loopback_and_disables_upstream_caches(self):
        spec = omlx_process_spec(executable=self.executable, app_support=self.root)
        self.assertEqual(spec.arguments[spec.arguments.index("--host") + 1], "127.0.0.1")
        self.assertIn("--no-hf-cache", spec.arguments)
        self.assertIn("--no-cache", spec.arguments)
        self.assertEqual(spec.environment["NO_PROXY"], "127.0.0.1,localhost,::1")

    def test_non_loopback_or_privileged_port_is_rejected(self):
        with self.assertRaisesRegex(ProcessPolicyError, "loopback"):
            omlx_process_spec(executable=self.executable, app_support=self.root, host="0.0.0.0")
        with self.assertRaisesRegex(ProcessPolicyError, "between 1024"):
            omlx_process_spec(executable=self.executable, app_support=self.root, port=80)

    def test_relative_paths_are_rejected(self):
        with self.assertRaisesRegex(ProcessPolicyError, "absolute"):
            omlx_process_spec(executable=Path("omlx"), app_support=self.root)

    def test_secret_value_cannot_enter_audit_representation(self):
        spec = omlx_process_spec(executable=self.executable, app_support=self.root)
        audit = spec.redacted()
        self.assertEqual(audit["secret_environment_names"], ["OMLX_API_KEY"])
        self.assertNotIn("OMLX_API_KEY", audit["environment"])
        self.assertNotIn("example-key-value", repr(audit))
        self.assertFalse(audit["inherit_parent_environment"])


if __name__ == "__main__":
    unittest.main()
