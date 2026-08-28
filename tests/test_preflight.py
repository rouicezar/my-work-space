import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import preflight


ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def profiles(self):
        return preflight.load_profiles(ROOT / "config/hardware-profiles.yaml")

    def test_profiles_are_versioned_and_provisional(self):
        items = self.profiles()
        self.assertEqual([item["minimum_memory_gib"] for item in items], [16, 32, 64])
        self.assertTrue(all(item["status"] == "provisional" for item in items))

    def test_choose_highest_eligible_profile(self):
        items = self.profiles()
        selected = preflight.choose_profile(items, 48 * preflight.GIB, 100 * preflight.GIB)
        self.assertEqual(selected, items[1])

    def test_no_profile_when_measurement_unknown(self):
        self.assertIsNone(preflight.choose_profile(self.profiles(), None, 100 * preflight.GIB))

    def test_report_distinguishes_unknown_from_unsupported(self):
        with (
            patch.object(preflight.platform, "machine", return_value="arm64"),
            patch.object(preflight, "macos_version", return_value=preflight.ProbeValue("26.0")),
            patch.object(preflight, "memory_bytes", return_value=preflight.ProbeValue(None, "permission denied")),
            patch.object(preflight, "free_disk_bytes", return_value=preflight.ProbeValue(100 * preflight.GIB)),
            patch.object(preflight, "port_available", return_value=preflight.ProbeValue(True)),
        ):
            report = preflight.build_report(
                ROOT / "config/hardware-profiles.yaml", ROOT, (8000,)
            )
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(report["unknowns"][0]["code"], "MEMORY_UNKNOWN")

    def test_report_rejects_non_apple_silicon(self):
        with (
            patch.object(preflight.platform, "machine", return_value="x86_64"),
            patch.object(preflight, "macos_version", return_value=preflight.ProbeValue("15.0")),
            patch.object(preflight, "memory_bytes", return_value=preflight.ProbeValue(64 * preflight.GIB)),
            patch.object(preflight, "free_disk_bytes", return_value=preflight.ProbeValue(200 * preflight.GIB)),
            patch.object(preflight, "port_available", return_value=preflight.ProbeValue(True)),
        ):
            report = preflight.build_report(
                ROOT / "config/hardware-profiles.yaml", ROOT, (8000,)
            )
        self.assertEqual(report["status"], "unsupported")
        self.assertEqual(report["blockers"][0]["code"], "UNSUPPORTED_ARCH")

    def test_profile_file_is_json_compatible_yaml(self):
        data = json.loads((ROOT / "config/hardware-profiles.yaml").read_text())
        self.assertEqual(data["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
