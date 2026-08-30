import unittest

from forma_ai.adapter_contract import AdapterIdentity, HealthEnvelope


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


if __name__ == "__main__":
    unittest.main()
