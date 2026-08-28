import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UpstreamManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "config/upstreams.json").read_text())
        cls.components = {item["id"]: item for item in cls.data["components"]}

    def test_manifest_is_versioned_and_complete(self):
        self.assertEqual(self.data["schema_version"], 1)
        self.assertEqual(set(self.components), {"semantica", "holaos", "herdr", "omlx"})

    def test_repositories_are_canonical_https_urls(self):
        for component in self.components.values():
            self.assertTrue(component["repository"].startswith("https://github.com/"))
        self.assertEqual(self.components["herdr"]["repository"], "https://github.com/herdrdev/herdr")

    def test_stable_bundle_candidates_are_pinned(self):
        for name in ("semantica", "herdr"):
            self.assertRegex(self.components[name]["release"], r"^v\d+\.\d+\.\d+$")

    def test_holaos_is_not_cleared_for_embedding(self):
        holaos = self.components["holaos"]
        self.assertNotEqual(holaos["license"], "Apache-2.0")
        self.assertEqual(
            holaos["distribution_policy"],
            "external_install_only_pending_written_clearance",
        )

    def test_every_component_has_distribution_reason(self):
        for component in self.components.values():
            self.assertTrue(component["distribution_policy"])
            self.assertGreater(len(component["reason"]), 30)


if __name__ == "__main__":
    unittest.main()
