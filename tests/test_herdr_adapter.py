import unittest

from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.herdr_transport import (
    SUPPORTED_PROTOCOL,
    HerdrProtocolError,
    HerdrRequestError,
    HerdrTransportError,
)


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
    def test_prompt_targets_claimed_pane_and_preserves_identity(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": self._agent_info(pane_id="pane-001", revision=1),
                    "argv": ["qwen"],
                }
            if method == "agent.prompt":
                agent = self._agent_info(pane_id="pane-001", revision=2)
                agent["agent_status"] = "working"
                return {
                    "type": "agent_prompted",
                    "agent": agent,
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        started = adapter.spawn_task(
            task_id="task-001", correlation_id="corr-001",
            agent_name="forma-task-001", agent_kind="qwen", pane_id="pane-001",
        )
        prompted = adapter.prompt_task(
            run_id=started.run_id, text="reply exactly READY", timeout_ms=5000
        )

        self.assertEqual(prompted.run_id, started.run_id)
        self.assertEqual(prompted.workspace_id, started.workspace_id)
        self.assertEqual(prompted.terminal_id, started.terminal_id)
        self.assertEqual(prompted.state, "running")
        self.assertEqual(prompted.revision, 2)
        self.assertEqual(calls[-1], (
            "agent.prompt",
            {
                "target": "pane-001", "text": "reply exactly READY",
                "wait": {"until": ["working", "blocked", "idle"], "timeout_ms": 5000},
            },
        ))

    def test_spawn_waits_for_detected_idle_agent_when_launch_is_pending(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": {
                        "terminal_id": "terminal-001",
                        "agent_status": "unknown",
                        "workspace_id": "workspace-001",
                        "tab_id": "tab-001",
                        "pane_id": "pane-001",
                        "focused": False,
                        "revision": 0,
                        "launch_pending": True,
                    },
                }
            if method == "events.wait":
                return {
                    "type": "wait_matched",
                    "event": {
                        "event": "pane_agent_status_changed",
                        "data": {"pane_id": "pane-001", "agent_status": "idle"},
                    },
                }
            if method == "agent.get":
                return {
                    "type": "agent_info",
                    "agent": {
                        "terminal_id": "terminal-001",
                        "agent_status": "idle",
                        "workspace_id": "workspace-001",
                        "tab_id": "tab-001",
                        "pane_id": "pane-001",
                        "focused": False,
                        "revision": 1,
                        "interactive_ready": True,
                    },
                }
            raise AssertionError(method)

        adapter = HerdrAdapter(request=request)
        task = adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="fixture-agent",
            agent_kind="codex",
            pane_id="pane-001",
            startup_timeout_ms=5000,
        )

        self.assertEqual(task.state, "running")
        self.assertEqual(task.revision, 1)
        self.assertEqual(
            calls,
            [
                (
                    "agent.start",
                    {
                        "name": "fixture-agent",
                        "kind": "codex",
                        "pane_id": "pane-001",
                        "timeout_ms": 5000,
                    },
                ),
                (
                    "events.wait",
                    {
                        "match_event": {
                            "event": "pane_agent_status_changed",
                            "pane_id": "pane-001",
                            "agent_status": "idle",
                        },
                        "timeout_ms": 5000,
                    },
                ),
                ("agent.get", {"target": "pane-001"}),
            ],
        )

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
            {
                "name": "forma-task-001",
                "kind": "codex",
                "pane_id": "pane-001",
                "timeout_ms": 30000,
            },
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
            if method == "agent.get":
                return {
                    "type": "agent_info",
                    "agent": self._agent_info(pane_id="pane-001", revision=1),
                }
            if method == "pane.process_info":
                return {
                    "type": "pane_process_info",
                    "process_info": {
                        "pane_id": "pane-001",
                        "shell_pid": 7,
                        "foreground_processes": [{"pid": 42}],
                    },
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

    def test_status_rejects_replacement_terminal_before_it_can_be_cancelled(self):
        def request(method, params):
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": self._agent_info(
                        pane_id="pane-001",
                        revision=1,
                    ),
                }
            if method == "agent.get":
                replacement = self._agent_info(pane_id="pane-001", revision=2)
                replacement["terminal_id"] = "terminal-replacement"
                return {"type": "agent_info", "agent": replacement}
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        task = adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )

        with self.assertRaisesRegex(ValueError, "task identity changed"):
            adapter.task_status(task.run_id)

    def test_reclaim_snapshots_before_rebinding_exact_task_identity(self):
        def initial_request(method, params):
            self.assertEqual(method, "agent.start")
            self.assertEqual(params["pane_id"], "pane-001")
            return {
                "type": "agent_started",
                "agent": self._agent_info(pane_id="pane-001", revision=1),
            }

        original = HerdrAdapter(request=initial_request).spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )
        calls = []

        def reconnecting_request(method, params):
            calls.append((method, params))
            if method == "session.snapshot":
                agent = self._agent_info(pane_id="pane-001", revision=1)
                return {
                    "type": "session_snapshot",
                    "snapshot": {
                        "version": "0.8.2",
                        "protocol": 20,
                        "workspaces": [],
                        "tabs": [],
                        "panes": [agent],
                        "agents": [agent],
                        "layouts": [],
                    },
                }
            if method == "agent.get":
                self.assertEqual(params, {"target": "pane-001"})
                return {
                    "type": "agent_info",
                    "agent": self._agent_info(pane_id="pane-001", revision=1),
                }
            self.fail(f"unexpected method: {method}")

        reconnected = HerdrAdapter(request=reconnecting_request)

        reclaimed = reconnected.reclaim_task(task=original)
        refreshed = reconnected.task_status(original.run_id)

        self.assertEqual(reclaimed, original)
        self.assertEqual(refreshed, original)
        self.assertEqual(
            [method for method, _params in calls],
            ["session.snapshot", "agent.get", "agent.get"],
        )

    def test_reclaim_rejects_stale_revision_before_agent_lookup(self):
        def initial_request(method, _params):
            self.assertEqual(method, "agent.start")
            return {
                "type": "agent_started",
                "agent": self._agent_info(pane_id="pane-001", revision=1),
            }

        original = HerdrAdapter(request=initial_request).spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )
        calls = []

        def reconnecting_request(method, _params):
            calls.append(method)
            if method == "session.snapshot":
                stale_agent = self._agent_info(pane_id="pane-001", revision=2)
                return {
                    "type": "session_snapshot",
                    "snapshot": {
                        "version": "0.8.2",
                        "protocol": 20,
                        "workspaces": [],
                        "tabs": [],
                        "panes": [stale_agent],
                        "agents": [stale_agent],
                        "layouts": [],
                    },
                }
            self.fail(f"unexpected method: {method}")

        with self.assertRaises(ValueError):
            HerdrAdapter(request=reconnecting_request).reclaim_task(task=original)

        self.assertEqual(calls, ["session.snapshot"])

    def test_fresh_run_requires_a_new_pane_and_terminal(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": self._agent_info(
                        pane_id=params["pane_id"], revision=1
                    ),
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        original = adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )

        with self.assertRaises(ValueError):
            adapter.start_fresh_task(
                previous_task=original,
                correlation_id="corr-fresh-001",
                agent_name="forma-task-001",
                agent_kind="codex",
                pane_id="pane-001",
            )
        fresh = adapter.start_fresh_task(
            previous_task=original,
            correlation_id="corr-fresh-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-002",
        )

        self.assertEqual(fresh.task_id, original.task_id)
        self.assertNotEqual(fresh.run_id, original.run_id)
        self.assertNotEqual(fresh.pane_id, original.pane_id)
        self.assertNotEqual(fresh.terminal_id, original.terminal_id)
        self.assertEqual(
            calls[-1],
            (
                "agent.start",
                {
                    "name": "forma-task-001",
                    "kind": "codex",
                    "pane_id": "pane-002",
                    "timeout_ms": 30000,
                },
            ),
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

class HerdrAdapterLifecyclePolicyTests(unittest.TestCase):
    @staticmethod
    def _agent(*, terminal_id="terminal-001", state="idle", revision=1):
        return {
            "terminal_id": terminal_id,
            "agent_status": state,
            "workspace_id": "workspace-001",
            "tab_id": "tab-001",
            "pane_id": "pane-001",
            "focused": False,
            "revision": revision,
        }

    @staticmethod
    def _process_info(*, process_ids=(42,)):
        return {
            "type": "pane_process_info",
            "process_info": {
                "pane_id": "pane-001",
                "shell_pid": 7,
                "foreground_processes": [
                    {"pid": process_id} for process_id in process_ids
                ],
            },
        }

    def _spawn(self, adapter):
        return adapter.spawn_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="fixture-agent",
            agent_kind="codex",
            pane_id="pane-001",
        )

    def test_wait_and_bounded_read_map_official_agent_surfaces(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": self._agent(),
                }
            if method == "agent.wait":
                return {
                    "type": "agent_info",
                    "agent": self._agent(state="blocked", revision=2),
                }
            if method == "agent.read":
                return {
                    "type": "pane_read",
                    "read": {
                        "pane_id": "pane-001",
                        "workspace_id": "workspace-001",
                        "tab_id": "tab-001",
                        "revision": 0,
                        "source": "recent",
                        "format": "text",
                        "text": "Awaiting approval\\n",
                        "truncated": True,
                    },
                }
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        task = self._spawn(adapter)

        blocked = adapter.wait_for_task(
            run_id=task.run_id,
            until=("blocked",),
            timeout_ms=1_000,
        )
        output = adapter.read_task_output(
            run_id=task.run_id,
            source="recent",
            lines=3,
        )

        self.assertEqual(blocked.state, "blocked")
        self.assertEqual(blocked.revision, 2)
        self.assertEqual(output.text, "Awaiting approval\\n")
        self.assertTrue(output.truncated)
        self.assertEqual(
            calls,
            [
                (
                    "agent.start",
                    {
                        "name": "fixture-agent",
                        "kind": "codex",
                        "pane_id": "pane-001",
                        "timeout_ms": 30_000,
                    },
                ),
                (
                    "agent.wait",
                    {
                        "target": "pane-001",
                        "until": ["blocked"],
                        "timeout_ms": 1_000,
                    },
                ),
                (
                    "agent.read",
                    {
                        "target": "pane-001",
                        "source": "recent",
                        "lines": 3,
                        "format": "text",
                        "strip_ansi": True,
                    },
                ),
            ],
        )

    def test_force_close_requires_confirmed_graceful_claim(self):
        calls = []

        def request(method, params):
            calls.append((method, params))
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": self._agent(state="blocked"),
                }
            if method == "agent.get":
                if calls.count(("agent.get", {"target": "pane-001"})) == 3:
                    raise HerdrRequestError("agent_not_found", "agent target pane-001 not found")
                return {"type": "agent_info", "agent": self._agent(state="blocked")}
            if method == "pane.process_info":
                return self._process_info()
            if method == "pane.send_keys":
                return {"type": "ok"}
            if method == "pane.close":
                return {"type": "ok"}
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        task = self._spawn(adapter)
        graceful = adapter.cancel_task(
            run_id=task.run_id,
            correlation_id="corr-graceful",
            expected_revision=1,
        )

        with self.assertRaises(ValueError):
            adapter.force_cancel_task(
                run_id=task.run_id,
                correlation_id="corr-force",
                expected_revision=1,
                force_confirmed=False,
            )
        forced = adapter.force_cancel_task(
            run_id=task.run_id,
            correlation_id="corr-force",
            expected_revision=1,
            force_confirmed=True,
        )

        self.assertEqual(graceful.action, "graceful_interrupt")
        self.assertEqual(forced.action, "force_close")
        self.assertEqual(forced.state, "force_closed")
        with self.assertRaisesRegex(ValueError, "task is not claimed"):
            adapter.task_status(task.run_id)
        self.assertEqual(
            [method for method, _params in calls],
            [
                "agent.start",
                "agent.get",
                "pane.process_info",
                "pane.send_keys",
                "agent.get",
                "pane.process_info",
                "pane.close",
                "agent.get",
            ],
        )

    def test_force_close_rejects_changed_terminal_before_pane_close(self):
        calls = []
        get_count = 0

        def request(method, params):
            nonlocal get_count
            calls.append((method, params))
            if method == "agent.start":
                return {
                    "type": "agent_started",
                    "agent": self._agent(terminal_id="terminal-original", state="blocked"),
                }
            if method == "agent.get":
                get_count += 1
                terminal_id = "terminal-original" if get_count == 1 else "terminal-replacement"
                return {
                    "type": "agent_info",
                    "agent": self._agent(terminal_id=terminal_id, state="blocked"),
                }
            if method == "pane.process_info":
                return self._process_info()
            if method == "pane.send_keys":
                return {"type": "ok"}
            self.fail(f"unexpected method: {method}")

        adapter = HerdrAdapter(request=request)
        task = self._spawn(adapter)
        adapter.cancel_task(
            run_id=task.run_id,
            correlation_id="corr-graceful",
            expected_revision=1,
        )

        with self.assertRaises(ValueError):
            adapter.force_cancel_task(
                run_id=task.run_id,
                correlation_id="corr-force",
                expected_revision=1,
                force_confirmed=True,
            )

        self.assertNotIn("pane.close", [method for method, _params in calls])


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


def _session_snapshot_response():
    return {
        "type": "session_snapshot",
        "snapshot": {
            "version": "0.8.2",
            "protocol": SUPPORTED_PROTOCOL,
            "workspaces": [
                {
                    "workspace_id": "workspace-001",
                    "number": 1,
                    "label": "forma",
                    "focused": True,
                    "pane_count": 1,
                    "tab_count": 1,
                    "active_tab_id": "tab-001",
                    "agent_status": "working",
                }
            ],
            "tabs": [
                {
                    "tab_id": "tab-001",
                    "workspace_id": "workspace-001",
                    "number": 1,
                    "label": "tab",
                    "focused": True,
                    "pane_count": 1,
                    "agent_status": "working",
                }
            ],
            "panes": [
                {
                    "pane_id": "pane-001",
                    "terminal_id": "terminal-001",
                    "workspace_id": "workspace-001",
                    "tab_id": "tab-001",
                    "focused": True,
                    "agent_status": "working",
                    "revision": 3,
                }
            ],
            "layouts": [{"layout_version": 1}],
            "agents": [
                {
                    "terminal_id": "terminal-001",
                    "agent_status": "working",
                    "workspace_id": "workspace-001",
                    "tab_id": "tab-001",
                    "pane_id": "pane-001",
                    "focused": True,
                    "revision": 3,
                    "name": "codex",
                }
            ],
        },
    }


class HerdrAdapterSnapshotTests(unittest.TestCase):
    def _adapter(self, responses, calls):
        def request(method, params):
            calls.append((method, params))
            response = next(responses)
            if isinstance(response, Exception):
                raise response
            return response

        return HerdrAdapter(
            request=request,
            clock=lambda: "2026-09-01T00:00:00Z",
        )

    def test_snapshot_maps_herdr_session_state(self):
        calls = []
        adapter = self._adapter(iter([_session_snapshot_response()]), calls)

        snapshot = adapter.snapshot()

        self.assertEqual(calls, [("session.snapshot", {})])
        self.assertEqual(snapshot.version, "0.8.2")
        self.assertEqual(snapshot.protocol, SUPPORTED_PROTOCOL)
        self.assertEqual(len(snapshot.workspaces), 1)
        workspace = snapshot.workspaces[0]
        self.assertEqual(workspace.workspace_id, "workspace-001")
        self.assertEqual(workspace.label, "forma")
        self.assertEqual(workspace.active_tab_id, "tab-001")
        self.assertEqual(workspace.agent_status, "working")
        self.assertEqual(len(snapshot.tabs), 1)
        self.assertEqual(snapshot.tabs[0].tab_id, "tab-001")
        self.assertEqual(snapshot.tabs[0].agent_status, "working")
        self.assertEqual(len(snapshot.panes), 1)
        pane = snapshot.panes[0]
        self.assertEqual(pane.pane_id, "pane-001")
        self.assertEqual(pane.terminal_id, "terminal-001")
        self.assertEqual(pane.revision, 3)
        self.assertEqual(pane.agent_status, "working")
        self.assertEqual(len(snapshot.agents), 1)
        agent = snapshot.agents[0]
        self.assertEqual(agent.pane_id, "pane-001")
        self.assertEqual(agent.workspace_id, "workspace-001")
        self.assertEqual(agent.agent_status, "working")
        self.assertEqual(agent.revision, 3)
        self.assertEqual(len(snapshot.layouts), 1)

    def test_snapshot_rejects_unexpected_response_type(self):
        calls = []
        adapter = self._adapter(iter([{"type": "unexpected"}]), calls)

        with self.assertRaises(ValueError):
            adapter.snapshot()

    def test_snapshot_rejects_missing_snapshot_payload(self):
        calls = []
        adapter = self._adapter(iter([{"type": "session_snapshot"}]), calls)

        with self.assertRaises(ValueError):
            adapter.snapshot()


class HerdrAdapterWaitForEventTests(unittest.TestCase):
    def _adapter(self, responses, calls):
        def request(method, params):
            calls.append((method, params))
            response = next(responses)
            if isinstance(response, Exception):
                raise response
            return response

        return HerdrAdapter(
            request=request,
            clock=lambda: "2026-09-01T00:00:00Z",
        )

    def test_wait_for_event_sends_match_and_returns_event(self):
        calls = []
        match_event = {
            "event": "pane_agent_status_changed",
            "pane_id": "pane-001",
            "agent_status": "idle",
        }
        adapter = self._adapter(
            iter(
                [
                    {
                        "type": "wait_matched",
                        "event": {
                            "event": "pane_agent_status_changed",
                            "data": {
                                "pane_id": "pane-001",
                                "workspace_id": "workspace-001",
                                "agent_status": "idle",
                            },
                        },
                    }
                ]
            ),
            calls,
        )

        event = adapter.wait_for_event(
            match_event=match_event, timeout_ms=1000
        )

        self.assertEqual(
            calls,
            [
                (
                    "events.wait",
                    {
                        "match_event": {
                            "event": "pane_agent_status_changed",
                            "pane_id": "pane-001",
                            "agent_status": "idle",
                        },
                        "timeout_ms": 1000,
                    },
                )
            ],
        )
        self.assertEqual(event.kind, "pane_agent_status_changed")
        self.assertEqual(event.data["pane_id"], "pane-001")
        self.assertEqual(event.data["agent_status"], "idle")

    def test_wait_for_event_timeout_surfaces_request_error(self):
        calls = []
        adapter = self._adapter(
            iter(
                [
                    HerdrRequestError(
                        "timeout", "timed out waiting for event match"
                    )
                ]
            ),
            calls,
        )

        with self.assertRaises(HerdrRequestError) as ctx:
            adapter.wait_for_event(
                match_event={"event": "pane_agent_status_changed"},
                timeout_ms=50,
            )

        self.assertEqual(ctx.exception.code, "timeout")

    def test_wait_for_event_rejects_unexpected_response_type(self):
        calls = []
        adapter = self._adapter(iter([{"type": "unexpected"}]), calls)

        with self.assertRaises(ValueError):
            adapter.wait_for_event(
                match_event={"event": "pane_agent_status_changed"},
                timeout_ms=None,
            )


if __name__ == "__main__":
    unittest.main()
