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


class HerdrAdapterTaskTests(unittest.TestCase):
    def test_two_mock_tasks_have_stable_ids_and_observable_states(self):
        calls = []
        start_responses = iter(
            (
                {
                    "run_id": "run-001",
                    "workspace_id": "workspace-001",
                    "pane_id": "pane-001",
                    "state": "starting",
                    "revision": 1,
                },
                {
                    "run_id": "run-002",
                    "workspace_id": "workspace-002",
                    "pane_id": "pane-002",
                    "state": "starting",
                    "revision": 1,
                },
            )
        )

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return next(start_responses)
            if method == "agent.get":
                return {
                    "run_id": params["run_id"],
                    "workspace_id": f"workspace-{params['run_id'][-3:]}",
                    "pane_id": f"pane-{params['run_id'][-3:]}",
                    "state": "running",
                    "revision": 2,
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)

        first = adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_kind="codex",
            working_directory="/fixture/worktree-001",
        )
        second = adapter.spawn_task(
            task_id="task-002",
            correlation_id="corr-002",
            agent_kind="claude",
            working_directory="/fixture/worktree-002",
        )
        first_running = adapter.task_status(first.run_id)
        second_running = adapter.task_status(second.run_id)

        self.assertEqual((first.task_id, first.run_id), ("task-001", "run-001"))
        self.assertEqual((second.task_id, second.run_id), ("task-002", "run-002"))
        self.assertNotEqual(first.pane_id, second.pane_id)
        self.assertEqual(first_running.state, "running")
        self.assertEqual(second_running.state, "running")
        self.assertEqual(first_running.revision, 2)
        self.assertEqual(second_running.revision, 2)
        self.assertEqual(
            [method for method, _params in calls],
            ["agent.start", "agent.start", "agent.get", "agent.get"],
        )


if __name__ == "__main__":
    unittest.main()
