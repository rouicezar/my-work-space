"""Model routing decision tests: local-first eligibility and cloud approval escalation."""

import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from forma_ai.cloud_approval import CloudApprovalError, CloudApprovalStore
from forma_ai.cloud_catalog import load_cloud_provider
from forma_ai.inference_routing import (
    LocalProfile, TaskRequirements, create_cloud_proposal, decide_route,
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


class LocalFirstRoutingTests(unittest.TestCase):
    def test_eligible_local_profile_routes_local_without_escalation(self):
        decision = decide_route(requirements(), profile())
        self.assertEqual(decision.route, "local")
        self.assertEqual(decision.reasons, ())

    def test_ineligible_local_profile_requires_cloud_escalation(self):
        decision = decide_route(
            requirements(required_capabilities=frozenset({"tools"})),
            profile(capabilities=frozenset({"chat"})),
        )
        self.assertEqual(decision.route, "cloud_proposal_required")
        self.assertIn("required_capability_missing", decision.reasons)


class ApprovalEscalationTests(unittest.TestCase):
    def setUp(self):
        self.provider = load_cloud_provider(ROOT / "config/cloud-providers.json", "deepseek")
        self.now = datetime(2026, 8, 30, 12, tzinfo=timezone.utc)

    def _proposal(self):
        return create_cloud_proposal(
            correlation_id=str(uuid.uuid4()), provider=self.provider,
            model_id="deepseek-v4-flash", requirements=requirements(),
            reason_codes=("local_unhealthy",),
            outbound_body={
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": "route me to cloud"}],
                "max_tokens": 2000, "stream": False,
            },
            redactions=(), now=self.now,
        )

    def test_approval_is_one_shot_and_binds_exact_payload(self):
        item, payload = self._proposal()
        with tempfile.TemporaryDirectory() as directory:
            store = CloudApprovalStore(Path(directory))
            record = store.approve(item, maximum_cost_usd=item.estimated_cost.maximum, now=self.now)
            self.assertEqual(record.payload_sha256, item.payload_sha256)
            consumed = store.consume(item, payload, now=self.now)
            self.assertIsNotNone(consumed.consumed_at)
            with self.assertRaises(CloudApprovalError) as again:
                store.consume(item, payload, now=self.now)
            self.assertEqual(again.exception.code, "APPROVAL_ALREADY_CONSUMED")

    def test_approval_rejects_cost_below_maximum_estimate(self):
        item, _ = self._proposal()
        with tempfile.TemporaryDirectory() as directory:
            store = CloudApprovalStore(Path(directory))
            with self.assertRaises(CloudApprovalError) as raised:
                store.approve(item, maximum_cost_usd=item.estimated_cost.maximum / 2, now=self.now)
            self.assertEqual(raised.exception.code, "APPROVAL_COST_TOO_LOW")

    def test_consume_rejects_tampered_payload(self):
        item, _ = self._proposal()
        with tempfile.TemporaryDirectory() as directory:
            store = CloudApprovalStore(Path(directory))
            store.approve(item, maximum_cost_usd=item.estimated_cost.maximum, now=self.now)
            with self.assertRaises(CloudApprovalError) as raised:
                store.consume(item, b"tampered", now=self.now)
            self.assertEqual(raised.exception.code, "APPROVAL_BINDING_MISMATCH")

    def test_consume_rejects_expired_approval(self):
        item, payload = self._proposal()
        with tempfile.TemporaryDirectory() as directory:
            store = CloudApprovalStore(Path(directory))
            store.approve(
                item, maximum_cost_usd=item.estimated_cost.maximum, now=self.now, ttl_seconds=1,
            )
            later = self.now + timedelta(seconds=2)
            with self.assertRaises(CloudApprovalError) as raised:
                store.consume(item, payload, now=later)
            self.assertEqual(raised.exception.code, "APPROVAL_EXPIRED")


if __name__ == "__main__":
    unittest.main()
