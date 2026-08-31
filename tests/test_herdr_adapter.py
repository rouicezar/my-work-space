import unittest

from forma_ai.herdr_adapter import HerdrAdapter


class HerdrAdapterAvailabilityTests(unittest.TestCase):
    def test_missing_binary_is_unavailable_without_claiming_runtime_health(self):
        adapter = HerdrAdapter(
            executable_finder=lambda _name: None,
            clock=lambda: "2026-08-31T00:00:00Z",
        )

        availability = adapter.availability()

        self.assertEqual(availability.identity.upstream_id, "herdr")
        self.assertEqual(availability.identity.upstream_version, "0.8.2")
        self.assertFalse(availability.installed)
        self.assertIsNone(availability.executable_path)
        self.assertEqual(availability.health.status, "unavailable")
        self.assertFalse(availability.health.reachable)
        self.assertFalse(availability.health.ready)
        self.assertEqual(availability.health.proof, "binary_not_found")
        self.assertEqual(availability.health.reason_code, "HERDR_BINARY_NOT_FOUND")

    def test_discovered_binary_is_only_availability_evidence(self):
        adapter = HerdrAdapter(
            executable_finder=lambda name: f"/fixture/bin/{name}",
            clock=lambda: "2026-08-31T00:00:00Z",
        )

        availability = adapter.availability()

        self.assertTrue(availability.installed)
        self.assertEqual(availability.executable_path, "/fixture/bin/herdr")
        self.assertEqual(availability.health.status, "unknown")
        self.assertFalse(availability.health.reachable)
        self.assertFalse(availability.health.ready)
        self.assertEqual(availability.health.proof, "binary_discovered_only")
        self.assertEqual(availability.health.reason_code, "HERDR_HEALTH_NOT_PROBED")


if __name__ == "__main__":
    unittest.main()
