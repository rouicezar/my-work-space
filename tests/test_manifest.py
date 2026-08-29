import copy
import json
import unittest
from pathlib import Path

from mac_ai_work_os.manifest import ManifestError, load_manifest, ordered_components, validate_manifest
from mac_ai_work_os.broker import BrokerPolicy


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
        ports.extend(item["port"] for item in self.manifest["product_services"])
        self.assertEqual(len(ports), len(set(ports)))

    def test_inference_broker_is_loopback_keychain_and_pinned_to_reviewed_evidence(self):
        broker = self.manifest["product_services"][0]
        self.assertEqual(broker["id"], "inference-broker")
        self.assertEqual(broker["bind_policy"], "loopback-only")
        self.assertEqual(broker["secret_policy"], "keychain-runtime-injection")
        self.assertEqual(broker["contract"], "verified-synthetic-loopback")
        self.assertEqual(broker["real_upstream_contract"], "verified-pinned-omlx-shallow-2026-08-29")
        defaults = BrokerPolicy("x" * 32)
        self.assertEqual(broker["max_request_bytes"], defaults.max_body_bytes)
        self.assertEqual(broker["max_response_bytes"], defaults.max_response_bytes)
        self.assertEqual(broker["max_concurrent_requests"], defaults.max_concurrent_requests)
        self.assertEqual(broker["max_concurrent_inference"], defaults.max_concurrent_inference)
        self.assertEqual(
            broker["inference_requests_per_minute"], defaults.inference_requests_per_minute
        )

    def test_inference_broker_resource_limits_fail_closed(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["product_services"][0]["max_concurrent_inference"] = 17
        with self.assertRaisesRegex(ManifestError, "cannot exceed"):
            validate_manifest(invalid)

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

    def test_omlx_evidence_is_layered_and_does_not_claim_deep_readiness(self):
        omlx = next(item for item in self.manifest["components"] if item["id"] == "omlx")
        self.assertTrue(omlx["artifact_contract"].startswith("verified-"))
        self.assertTrue(omlx["shallow_health_contract"].startswith("verified-"))
        self.assertEqual(omlx["deep_health_contract"], "pending-real-model-inference")
        self.assertEqual(
            omlx["isolation_contract"],
            "shallow-verified-product-home-2026-08-29-full-fs-audit-pending",
        )
        self.assertEqual(omlx["health_contract"], "pending-adapter-verification")


if __name__ == "__main__":
    unittest.main()
