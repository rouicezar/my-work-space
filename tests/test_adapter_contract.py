import unittest

from forma_ai.adapter_contract import (
    AdapterIdentity,
    AuditEnvelope,
    CapabilityDeclaration,
    HealthEnvelope,
    PolicyPreview,
)


class AdapterIdentityAndHealthContractTests(unittest.TestCase):
    def test_identity_is_stable_vendor_neutral_and_serializable(self):
        identity = AdapterIdentity(
            adapter_id="local-inference",
            adapter_version="1.0.0",
            protocol_version="1",
            upstream_id="omlx",
            upstream_version="0.6.3",
        )

        self.assertEqual(identity.to_dict(), {
            "adapter_id": "local-inference",
            "adapter_version": "1.0.0",
            "protocol_version": "1",
            "upstream_id": "omlx",
            "upstream_version": "0.6.3",
        })

    def test_health_separates_reachability_readiness_and_real_proof(self):
        health = HealthEnvelope(
            schema_version=1,
            status="degraded",
            reachable=True,
            ready=False,
            proof="shallow",
            checked_at="2026-08-31T12:00:00Z",
            reason_code="INFERENCE_UNVERIFIED",
        )

        self.assertEqual(health.to_dict(), {
            "schema_version": 1,
            "status": "degraded",
            "reachable": True,
            "ready": False,
            "proof": "shallow",
            "checked_at": "2026-08-31T12:00:00Z",
            "reason_code": "INFERENCE_UNVERIFIED",
        })

    def test_capability_declaration_names_operations_and_proof(self):
        capability = CapabilityDeclaration(
            capability_id="agent_execution",
            operations=("dispatch", "status", "cancel", "resume"),
            proof="contract_tested",
        )

        self.assertEqual(capability.to_dict(), {
            "capability_id": "agent_execution",
            "operations": ["dispatch", "status", "cancel", "resume"],
            "proof": "contract_tested",
        })

    def test_policy_preview_binds_exact_payload_and_approval_boundary(self):
        preview = PolicyPreview(
            correlation_id="run-123",
            action="cloud.inference",
            data_classes=("user_text",),
            external_write=True,
            approval_required=True,
            payload_sha256="a" * 64,
        )

        self.assertEqual(preview.to_dict(), {
            "correlation_id": "run-123",
            "action": "cloud.inference",
            "data_classes": ["user_text"],
            "external_write": True,
            "approval_required": True,
            "payload_sha256": "a" * 64,
        })

    def test_audit_envelope_is_correlated_and_redaction_explicit(self):
        audit = AuditEnvelope(
            event_id="event-123",
            correlation_id="run-123",
            action="cloud.inference",
            outcome="approved",
            occurred_at="2026-08-31T12:00:00Z",
            redacted_fields=("prompt", "credential"),
        )

        self.assertEqual(audit.to_dict(), {
            "event_id": "event-123",
            "correlation_id": "run-123",
            "action": "cloud.inference",
            "outcome": "approved",
            "occurred_at": "2026-08-31T12:00:00Z",
            "redacted_fields": ["prompt", "credential"],
        })


if __name__ == "__main__":
    unittest.main()
