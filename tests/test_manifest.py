import copy
import json
import unittest
from pathlib import Path

from mac_ai_work_os.manifest import ManifestError, load_manifest, ordered_components, validate_manifest


ROOT = Path(__file__).resolve().parents[1]


class ProductManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest(ROOT / "config/product-manifest.json")

    def test_start_order_places_inference_before_memory_and_agents(self):
        ids = [item["id"] for item in ordered_components(self.manifest)]
        self.assertEqual(ids, ["omlx", "semantica", "herdr", "holaos"])

    def test_stop_order_is_reverse_start_order(self):
        ids = [item["id"] for item in ordered_components(self.manifest, reverse=True)]
        self.assertEqual(ids, ["holaos", "herdr", "semantica", "omlx"])

    def test_ports_do_not_collide(self):
        ports = [item["port"] for item in self.manifest["components"] if item["port"]]
        self.assertEqual(len(ports), len(set(ports)))

    def test_self_update_bypass_is_rejected(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["components"][0]["allow_self_update"] = True
        with self.assertRaisesRegex(ManifestError, "self-update"):
            validate_manifest(invalid)

    def test_filesystem_secrets_are_rejected(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["paths"]["secrets"] = "${APP_SUPPORT}/secrets"
        with self.assertRaisesRegex(ManifestError, "Keychain"):
            validate_manifest(invalid)

    def test_unverified_health_contract_cannot_be_promoted_in_manifest_only(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["components"][1]["health_contract"] = "verified"
        with self.assertRaisesRegex(ManifestError, "adapter evidence"):
            validate_manifest(invalid)

    def test_component_versions_match_verified_upstream_manifest(self):
        upstream_data = json.loads((ROOT / "config/upstreams.json").read_text())
        upstream_versions = {item["id"]: item["release"] for item in upstream_data["components"]}
        product_versions = {item["id"]: item["version"] for item in self.manifest["components"]}
        self.assertEqual(product_versions, upstream_versions)

    def test_holaos_distribution_boundary_is_preserved(self):
        holaos = next(item for item in self.manifest["components"] if item["id"] == "holaos")
        self.assertEqual(
            holaos["install_mode"],
            "external_user_install_pending_license_clearance",
        )


if __name__ == "__main__":
    unittest.main()
