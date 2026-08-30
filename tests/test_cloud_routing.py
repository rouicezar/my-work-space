import json
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from forma_ai.cloud_catalog import CloudCatalogError, load_cloud_provider
from forma_ai.inference_routing import (
    LocalProfile, RoutingError, TaskRequirements, create_cloud_proposal, decide_route,
)


ROOT = Path(__file__).resolve().parents[1]


def requirements(**changes):
    values = {
        "estimated_input_tokens": 10_000,
        "maximum_output_tokens": 2_000,
        "required_capabilities": frozenset({"chat"}),
        "minimum_available_memory_mb": 1024,
        "data_classes": frozenset({"user_text"}),
    }
    values.update(changes)
    return TaskRequirements(**values)


def profile(**changes):
    values = {
        "verified": True, "healthy": True, "context_window_tokens": 32_768,
        "capabilities": frozenset({"chat"}), "available_memory_mb": 4096,
    }
    values.update(changes)
    return LocalProfile(**values)


class CloudRoutingTests(unittest.TestCase):
    def setUp(self):
        self.provider = load_cloud_provider(ROOT / "config/cloud-providers.json", "deepseek")
        self.now = datetime(2026, 8, 30, 12, tzinfo=timezone.utc)

    def test_real_catalog_is_disabled_replaceable_and_current_at_evidence_time(self):
        self.assertFalse(self.provider.enabled_by_default)
        self.assertEqual(self.provider.origin, "https://api.deepseek.com")
        self.assertEqual(self.provider.model("deepseek-v4-flash").maximum_output_tokens, 384000)
        self.assertTrue(self.provider.pricing_is_current(self.now))
        self.assertEqual(self.provider.training_opt_out_state, "unknown")

    def test_local_route_requires_every_verified_boundary(self):
        self.assertEqual(decide_route(requirements(), profile()).route, "local")
        decision = decide_route(
            requirements(required_capabilities=frozenset({"chat", "tools"})),
            profile(healthy=False, available_memory_mb=512),
        )
        self.assertEqual(decision.route, "cloud_proposal_required")
        self.assertEqual(decision.reasons, (
            "local_unhealthy", "required_capability_missing", "local_resource_insufficient",
        ))

    def test_proposal_binds_exact_canonical_payload_privacy_and_conservative_cost(self):
        body = {"messages": [{"content": "你好", "role": "user"}],
                "model": "deepseek-v4-flash", "max_tokens": 2000, "stream": False}
        proposal, serialized = create_cloud_proposal(
            correlation_id=str(uuid.uuid4()), provider=self.provider,
            model_id="deepseek-v4-flash", requirements=requirements(),
            reason_codes=("required_capability_missing",), outbound_body=body,
            redactions=("removed-email-address",), now=self.now,
        )
        self.assertEqual(serialized, json.dumps(
            body, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode())
        self.assertEqual(len(proposal.payload_sha256), 64)
        self.assertEqual(proposal.processing_location, "People's Republic of China")
        self.assertEqual(proposal.estimated_cost.currency, "USD")
        self.assertLess(proposal.estimated_cost.minimum, proposal.estimated_cost.maximum)

    def test_sensitive_classes_are_blocked_before_serialization(self):
        with self.assertRaisesRegex(RoutingError, "credentials") as raised:
            create_cloud_proposal(
                correlation_id=str(uuid.uuid4()), provider=self.provider,
                model_id="deepseek-v4-flash",
                requirements=requirements(data_classes=frozenset({"credentials"})),
                reason_codes=("local_unhealthy",), outbound_body={"secret": "must-not-send"},
                redactions=(), now=self.now,
            )
        self.assertEqual(raised.exception.code, "CLOUD_DATA_CLASS_BLOCKED")

    def test_payload_contract_binds_model_output_limit_and_non_streaming_shape(self):
        for body in (
            {"model": "wrong", "messages": [{"role": "user", "content": "x"}], "max_tokens": 2000, "stream": False},
            {"model": "deepseek-v4-flash", "messages": [], "max_tokens": 2000, "stream": False},
            {"model": "deepseek-v4-flash", "messages": [{"role": "user", "content": "x"}], "max_tokens": 1, "stream": False},
            {"model": "deepseek-v4-flash", "messages": [{"role": "user", "content": "x"}], "max_tokens": 2000, "stream": True},
        ):
            with self.subTest(body=body), self.assertRaises(RoutingError) as raised:
                create_cloud_proposal(
                    correlation_id=str(uuid.uuid4()), provider=self.provider,
                    model_id="deepseek-v4-flash", requirements=requirements(),
                    reason_codes=("local_unhealthy",), outbound_body=body,
                    redactions=(), now=self.now,
                )
            self.assertEqual(raised.exception.code, "CLOUD_PAYLOAD_CONTRACT_INVALID")

    def test_stale_price_blocks_cloud_proposal(self):
        stale = self.provider.pricing_effective_at + timedelta(hours=169)
        with self.assertRaises(RoutingError) as raised:
            create_cloud_proposal(
                correlation_id=str(uuid.uuid4()), provider=self.provider,
                model_id="deepseek-v4-flash", requirements=requirements(),
                reason_codes=("local_unhealthy",), outbound_body={
                    "model": "deepseek-v4-flash",
                    "messages": [{"role": "user", "content": "x"}],
                    "max_tokens": 2000, "stream": False,
                },
                redactions=(), now=stale,
            )
        self.assertEqual(raised.exception.code, "CLOUD_PRICING_STALE")

    def test_catalog_rejects_enabled_by_default_and_non_https_origin(self):
        source = json.loads((ROOT / "config/cloud-providers.json").read_text())
        for field, value, code in (
            ("enabled_by_default", True, "CLOUD_PROVIDER_UNSAFE_DEFAULT"),
            ("origin", "http://api.deepseek.com", "CLOUD_ORIGIN_INVALID"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                copy = json.loads(json.dumps(source))
                copy["providers"][0][field] = value
                path = Path(directory) / "catalog.json"
                path.write_text(json.dumps(copy))
                with self.assertRaises(CloudCatalogError) as raised:
                    load_cloud_provider(path, "deepseek")
                self.assertEqual(raised.exception.code, code)


if __name__ == "__main__":
    unittest.main()
