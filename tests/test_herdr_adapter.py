import unittest

from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.herdr_transport import HerdrProtocolError, HerdrTransportError


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
                    "type": "agent_started",
                    "agent": {
                        "terminal_id": "terminal-001",
                        "agent_status": "unknown",
                        "workspace_id": "workspace-001",
                        "tab_id": "tab-001",
                        "pane_id": "pane-001",
                        "focused": False,
                        "revision": 1,
                    },
                    "argv": ["codex"],
                },
                {
                    "type": "agent_started",
                    "agent": {
                        "terminal_id": "terminal-002",
                        "agent_status": "unknown",
                        "workspace_id": "workspace-002",
                        "tab_id": "tab-002",
                        "pane_id": "pane-002",
                        "focused": False,
                        "revision": 1,
                    },
                    "argv": ["claude"],
                },
            )
        )

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return next(start_responses)
            if method == "agent.get":
                return {
                    "type": "agent_info",
                    "agent": {
                        "terminal_id": f"terminal-{params['target'][-3:]}",
                        "agent_status": "working",
                        "workspace_id": f"workspace-{params['target'][-3:]}",
                        "tab_id": f"tab-{params['target'][-3:]}",
                        "pane_id": params["target"],
                        "focused": False,
                        "revision": 2,
                    },
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)

        first = adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )
        second = adapter.spawn_task(
            task_id="task-002",
            correlation_id="corr-002",
            agent_name="forma-task-002",
            agent_kind="claude",
            pane_id="pane-002",
        )
        first_running = adapter.task_status(first.run_id)
        second_running = adapter.task_status(second.run_id)

        self.assertEqual(
            (first.task_id, first.run_id), ("task-001", "herdr:task-001:pane-001")
        )
        self.assertEqual(
            (second.task_id, second.run_id), ("task-002", "herdr:task-002:pane-002")
        )
        self.assertNotEqual(first.pane_id, second.pane_id)
        self.assertEqual(first_running.state, "running")
        self.assertEqual(second_running.state, "running")
        self.assertEqual(first_running.revision, 2)
        self.assertEqual(second_running.revision, 2)
        self.assertEqual(
            [method for method, _params in calls],
            ["agent.start", "agent.start", "agent.get", "agent.get"],
        )
        self.assertEqual(
            calls[0][1],
            {"name": "forma-task-001", "kind": "codex", "pane_id": "pane-001"},
        )
        self.assertEqual(calls[2][1], {"target": "pane-001"})

    def test_graceful_cancel_targets_the_exact_pane(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": self._agent_info(pane_id="pane-001", revision=1),
                    "argv": ["codex"],
                }
            if method == "pane.send_keys":
                return {"type": "ok"}
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        task = adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )

        result = adapter.cancel_task(
            run_id=task.run_id,
            correlation_id="corr-cancel-001",
            expected_revision=1,
        )

        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.run_id, task.run_id)
        self.assertEqual(result.action, "graceful_interrupt")
        self.assertEqual(result.state, "cancel_requested")
        self.assertEqual(calls[-1], ("pane.send_keys", {"pane_id": "pane-001", "keys": ["ctrl+c"]}))

    def test_native_resume_reconciles_session_and_revision_before_start(self):
        calls = []
        session_ref = {
            "source": "integration",
            "agent": "codex",
            "kind": "id",
            "value": "session-001",
        }
        start_count = 0

        def request(method, params):
            nonlocal start_count
            calls.append((method, params))
            if method == "agent.start":
                start_count += 1
                revision = start_count
                return {
                    "type": "agent_started",
                    "agent": self._agent_info(
                        pane_id="pane-001",
                        revision=revision,
                        session_ref=session_ref if revision == 1 else None,
                    ),
                    "argv": ["codex"],
                }
            if method == "agent.get":
                return {
                    "type": "agent_info",
                    "agent": self._agent_info(
                        pane_id="pane-001",
                        revision=1,
                        session_ref=session_ref,
                    ),
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        task = adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )

        result = adapter.resume_task(
            run_id=task.run_id,
            correlation_id="corr-resume-001",
            expected_revision=1,
            native_session_ref=session_ref,
            agent_name="forma-task-001",
            agent_kind="codex",
        )

        self.assertEqual(result.action, "native_resume")
        self.assertEqual(result.state, "starting")
        self.assertEqual(
            [method for method, _params in calls],
            ["agent.start", "agent.get", "agent.start"],
        )
        self.assertEqual(
            calls[-1][1],
            {"name": "forma-task-001", "kind": "codex", "pane_id": "pane-001"},
        )

    @staticmethod
    def _agent_info(*, pane_id, revision, session_ref=None):
        return {
            "terminal_id": f"terminal-{pane_id[-3:]}",
            "agent_status": "unknown",
            "workspace_id": f"workspace-{pane_id[-3:]}",
            "tab_id": f"tab-{pane_id[-3:]}",
            "pane_id": pane_id,
            "focused": False,
            "revision": revision,
            "agent_session": session_ref,
        }


class HerdrAdapterFixtureTests(unittest.TestCase):
    def test_open_workspace_sends_schema_params_and_extracts_ids(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            return {
                "type": "workspace_created",
                "workspace": {"workspace_id": "w1", "label": "forma-p3t12"},
                "tab": {"tab_id": "w1:t1"},
                "root_pane": {
                    "pane_id": "w1:p1",
                    "workspace_id": "w1",
                    "tab_id": "w1:t1",
                },
            }

        adapter = HerdrAdapter(request=request)

        workspace = adapter.open_workspace(cwd="/fixtures/a", label="forma-p3t12")

        self.assertEqual(
            calls,
            [("workspace.create", {"cwd": "/fixtures/a", "label": "forma-p3t12"})],
        )
        self.assertEqual(workspace.workspace_id, "w1")
        self.assertEqual(workspace.root_pane_id, "w1:p1")

    def test_open_workspace_without_optional_params_sends_empty_params(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            return {
                "type": "workspace_created",
                "workspace": {"workspace_id": "w1"},
                "tab": {"tab_id": "w1:t1"},
                "root_pane": {"pane_id": "w1:p1"},
            }

        adapter = HerdrAdapter(request=request)

        workspace = adapter.open_workspace()

        self.assertEqual(calls, [("workspace.create", {})])
        self.assertEqual(workspace.workspace_id, "w1")
        self.assertEqual(workspace.root_pane_id, "w1:p1")

    def test_open_pane_sends_schema_params_and_extracts_ids(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            return {
                "type": "pane_info",
                "pane": {"pane_id": "w1:p2", "workspace_id": "w1"},
            }

        adapter = HerdrAdapter(request=request)

        pane = adapter.open_pane(
            direction="right",
            target_pane_id="w1:p1",
            cwd="/fixtures/b",
        )

        self.assertEqual(
            calls,
            [
                (
                    "pane.split",
                    {
                        "direction": "right",
                        "target_pane_id": "w1:p1",
                        "cwd": "/fixtures/b",
                    },
                )
            ],
        )
        self.assertEqual(pane.pane_id, "w1:p2")
        self.assertEqual(pane.workspace_id, "w1")

    def test_spawn_reported_task_drives_reports_and_registers_lifecycle(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method == "pane.send_text":
                return {"type": "ok"}
            if method == "pane.report_agent":
                return {"type": "ok"}
            if method == "agent.get":
                return {
                    "type": "agent_info",
                    "agent": {
                        "terminal_id": "term-001",
                        "agent_status": "working",
                        "workspace_id": "w1",
                        "tab_id": "w1:t1",
                        "pane_id": "w1:p1",
                        "focused": False,
                        "revision": 3,
                    },
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)

        task = adapter.spawn_reported_task(
            task_id="task-a",
            correlation_id="corr-a",
            agent_name="fixture-agent-a",
            pane_id="w1:p1",
            command="date +%s > a_start.txt; sleep 8\n",
        )

        self.assertEqual(
            [method for method, _params in calls],
            ["pane.send_text", "pane.report_agent", "agent.get"],
        )
        self.assertEqual(
            calls[0][1],
            {"pane_id": "w1:p1", "text": "date +%s > a_start.txt; sleep 8\n"},
        )
        self.assertEqual(
            calls[1][1],
            {
                "pane_id": "w1:p1",
                "source": "forma-fixture",
                "agent": "fixture-agent-a",
                "state": "working",
            },
        )
        self.assertEqual(calls[2][1], {"target": "w1:p1"})
        self.assertEqual(task.task_id, "task-a")
        self.assertEqual(task.run_id, "herdr:task-a:w1:p1")
        self.assertEqual(task.pane_id, "w1:p1")
        self.assertEqual(task.state, "running")
        self.assertEqual(task.revision, 3)

    def test_spawned_fixture_task_cancels_through_existing_lifecycle(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method in ("pane.send_text", "pane.report_agent", "pane.send_keys"):
                return {"type": "ok"}
            if method == "agent.get":
                return {
                    "type": "agent_info",
                    "agent": {
                        "terminal_id": "term-001",
                        "agent_status": "working",
                        "workspace_id": "w1",
                        "tab_id": "w1:t1",
                        "pane_id": "w1:p1",
                        "focused": False,
                        "revision": 3,
                    },
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        task = adapter.spawn_reported_task(
            task_id="task-a",
            correlation_id="corr-a",
            agent_name="fixture-agent-a",
            pane_id="w1:p1",
            command="sleep 8\n",
        )

        result = adapter.cancel_task(
            run_id=task.run_id,
            correlation_id="corr-cancel-a",
            expected_revision=task.revision,
        )

        self.assertEqual(result.action, "graceful_interrupt")
        self.assertEqual(result.state, "cancel_requested")
        self.assertEqual(
            calls[-1],
            ("pane.send_keys", {"pane_id": "w1:p1", "keys": ["ctrl+c"]}),
        )


class HerdrAdapterProbeTests(unittest.TestCase):
    def _adapter(self, probe):
        return HerdrAdapter(
            executable_finder=lambda _name: "/fixture/bin/herdr",
            clock=lambda: "2026-09-01T00:00:00Z",
            probe=probe,
        )

    def test_ready_probe_reports_reachable_and_ready(self):
        adapter = self._adapter(
            lambda: {"type": "pong", "version": "0.8.2", "protocol": 20}
        )

        availability = adapter.availability()

        self.assertTrue(availability.installed)
        self.assertEqual(availability.health.status, "ready")
        self.assertTrue(availability.health.reachable)
        self.assertTrue(availability.health.ready)
        self.assertEqual(availability.health.proof, "ping_pong_verified")
        self.assertEqual(availability.health.reason_code, "")
        self.assertEqual(availability.health.checked_at, "2026-09-01T00:00:00Z")

    def test_protocol_incompatible_probe_fails_closed(self):
        def probe():
            raise HerdrProtocolError("Herdr server protocol 19 is not supported")

        health = self._adapter(probe).availability().health

        self.assertEqual(health.status, "incompatible")
        self.assertTrue(health.reachable)
        self.assertFalse(health.ready)
        self.assertEqual(health.proof, "protocol_mismatch")
        self.assertEqual(health.reason_code, "HERDR_PROTOCOL_INCOMPATIBLE")

    def test_unreachable_probe_fails_closed(self):
        def probe():
            raise HerdrTransportError("connection refused")

        health = self._adapter(probe).availability().health

        self.assertEqual(health.status, "unreachable")
        self.assertFalse(health.reachable)
        self.assertFalse(health.ready)
        self.assertEqual(health.proof, "socket_unreachable")
        self.assertEqual(health.reason_code, "HERDR_SOCKET_UNREACHABLE")

    def test_os_error_from_probe_fails_closed_as_unreachable(self):
        def probe():
            raise FileNotFoundError("no such file or directory")

        health = self._adapter(probe).availability().health

        self.assertEqual(health.status, "unreachable")
        self.assertEqual(health.reason_code, "HERDR_SOCKET_UNREACHABLE")

    def test_non_pong_payload_fails_closed_as_incompatible(self):
        adapter = self._adapter(lambda: {"type": "unexpected"})

        health = adapter.availability().health

        self.assertEqual(health.status, "incompatible")
        self.assertEqual(health.proof, "protocol_mismatch")
        self.assertEqual(health.reason_code, "HERDR_PROTOCOL_INCOMPATIBLE")

    def test_missing_binary_with_live_probe_reports_probe_health(self):
        adapter = HerdrAdapter(
            executable_finder=lambda _name: None,
            clock=lambda: "2026-09-01T00:00:00Z",
            probe=lambda: {"type": "pong", "version": "0.8.2", "protocol": 20},
        )

        availability = adapter.availability()

        self.assertFalse(availability.installed)
        self.assertEqual(availability.health.status, "ready")
        self.assertTrue(availability.health.reachable)


if __name__ == "__main__":
    unittest.main()
