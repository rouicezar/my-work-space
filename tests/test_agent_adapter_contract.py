import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/agent-adapter.md"


class AgentAdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CONTRACT.read_text(encoding="utf-8")

    def test_all_required_operations_are_normative_sections(self):
        for operation in (
            "discover", "dispatch", "status", "handoff",
            "cancel", "resume", "artifacts", "audit",
        ):
            with self.subTest(operation=operation):
                self.assertIn(f"## Required operation: {operation}", self.text)

    def test_runtime_authority_and_recovery_cannot_be_downgraded(self):
        for requirement in (
            "Herdr is the authoritative execution runtime",
            "fresh Herdr snapshot",
            "Closing the Forma AI window is not cancellation",
            "fails closed",
            "Semantica remains the governed long-term knowledge authority",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_policy_audit_and_secret_boundaries_are_explicit(self):
        for requirement in (
            "one-shot approval",
            "policy-preview digest",
            "correlated audit event",
            "must not contain credentials",
            "raw prompts",
            "explicit redacted-field names",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_lifecycle_artifact_and_conformance_requirements_are_complete(self):
        for requirement in (
            "cancel_requested",
            "idempotency key",
            "expected revision",
            "artifact digest/ownership",
            "two parallel Herdr-backed fixture runs",
            "protocol mismatch",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)


if __name__ == "__main__":
    unittest.main()
