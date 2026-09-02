"""Live Herdr integration proofs against the verified Herdr binary."""

import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path

from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.herdr_presentation import HerdrPresentationProvider
from forma_ai.herdr_transport import (
    HerdrRequestError,
    HerdrSocketTransport,
    HerdrSubscriptionListener,
)


def _find_herdr_binary():
    candidates = (
        os.environ.get("FORMA_HERDR_TEST_BINARY"),
        os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "Forma AI",
            "cache",
            "downloads",
            "herdr-macos-aarch64",
        ),
    )
    return next((path for path in candidates if path and os.path.isfile(path)), None)


@unittest.skipUnless(
    _find_herdr_binary(), "verified Herdr artifact binary is not available"
)
class HerdrTwoFixtureAgentIntegrationTests(unittest.TestCase):
    WATCHDOG_SECONDS = 45.0

    def _stage(self, name):
        self.current_stage = name
        elapsed = time.monotonic() - self.started_at
        print(
            f"[P3-T12 {self.session_name}] {elapsed:05.1f}s {name}",
            file=sys.stderr,
            flush=True,
        )

    def _server_log_tail(self, lines=40):
        path = getattr(self, "server_output_path", None)
        if path is None or not path.exists():
            return "server output unavailable"
        text = path.read_text(encoding="utf-8", errors="replace")
        return "\n".join(text.splitlines()[-lines:]) or "server output empty"

    def _watchdog_expired(self, _signum, _frame):
        raise TimeoutError(
            f"P3-T12 exceeded {self.WATCHDOG_SECONDS:.0f}s during "
            f"{self.current_stage}\nHerdr server output tail:\n{self._server_log_tail()}"
        )

    def _callTestMethod(self, method):
        try:
            return super()._callTestMethod(method)
        except BaseException:
            self._stage(f"failed during {self.current_stage}")
            print(
                f"[P3-T12 {self.session_name}] Herdr server output tail:\n"
                f"{self._server_log_tail()}",
                file=sys.stderr,
                flush=True,
            )
            raise

    def setUp(self):
        self.started_at = time.monotonic()
        self.current_stage = "setup"
        self.binary = _find_herdr_binary()
        self.fixture_bin = Path(__file__).parent / "fixtures" / "herdr_agent_bin"
        self.temp_root = tempfile.TemporaryDirectory(prefix="forma-p3t12-test-")
        self.session_name = f"forma-p3t12-test-{uuid.uuid4().hex[:8]}"
        self.server_output_path = Path(self.temp_root.name) / "herdr-server-output.log"
        self.server_output_handle = self.server_output_path.open("wb")
        self.previous_alarm_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, self._watchdog_expired)
        signal.setitimer(signal.ITIMER_REAL, self.WATCHDOG_SECONDS)
        self.socket_path = os.path.join(
            os.path.expanduser("~"),
            ".config",
            "herdr",
            "sessions",
            self.session_name,
            "herdr.sock",
        )
        self.server = None
        try:
            self._stage("starting Herdr server")
            server_env = os.environ.copy()
            server_env["SHELL"] = "/bin/bash"
            server_env["PATH"] = (
                f"{self.fixture_bin}{os.pathsep}/usr/bin{os.pathsep}/bin"
            )
            self.server = subprocess.Popen(
                [self.binary, "--session", self.session_name, "server"],
                stdout=self.server_output_handle,
                stderr=subprocess.STDOUT,
                env=server_env,
            )
            deadline = time.monotonic() + 15.0
            while not os.path.exists(self.socket_path):
                if time.monotonic() > deadline:
                    raise AssertionError("Herdr test server socket did not appear")
                if self.server.poll() is not None:
                    raise AssertionError(
                        f"Herdr test server exited early with {self.server.returncode}"
                    )
                time.sleep(0.1)
            self._stage("Herdr socket ready")
            self.transport = HerdrSocketTransport(
                socket_path=self.socket_path, environ={}, request_timeout=15.0
            )
            self.adapter = HerdrAdapter(
                executable_finder=lambda _name: self.binary,
                clock=lambda: "2026-09-01T00:00:00Z",
                request=self.transport,
                probe=self.transport.probe,
            )
        except Exception:
            print(self._server_log_tail(), file=sys.stderr, flush=True)
            self.tearDown()
            raise

    def tearDown(self):
        cleanup_errors = []
        if hasattr(self, "started_at") and hasattr(self, "session_name"):
            self._stage("cleanup started")
        for args in (
            ["session", "stop", self.session_name, "--json"],
            ["session", "delete", self.session_name, "--json"],
        ):
            try:
                completed = subprocess.run(
                    [self.binary, *args],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if completed.returncode != 0:
                    cleanup_errors.append(
                        f"{' '.join(args)} exited {completed.returncode}: "
                        f"{completed.stderr.strip() or completed.stdout.strip()}"
                    )
            except subprocess.TimeoutExpired:
                cleanup_errors.append(f"{' '.join(args)} exceeded 10s")
        if self.server is not None and self.server.poll() is None:
            self.server.terminate()
            try:
                self.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server.kill()
                self.server.wait(timeout=5)
        if hasattr(self, "temp_root"):
            if hasattr(self, "server_output_handle"):
                self.server_output_handle.close()
            self.temp_root.cleanup()
        signal.setitimer(signal.ITIMER_REAL, 0)
        if hasattr(self, "previous_alarm_handler"):
            signal.signal(signal.SIGALRM, self.previous_alarm_handler)
        if hasattr(self, "started_at") and hasattr(self, "session_name"):
            self._stage("cleanup finished")
        if cleanup_errors:
            self.fail("; ".join(cleanup_errors))

    def _send_text(self, pane_id, text):
        response = self.transport(
            "pane.send_text", {"pane_id": pane_id, "text": text}
        )
        self.assertEqual(response["type"], "ok")

    def _wait_marker(self, pane_id, pattern):
        response = self.transport(
            "pane.wait_for_output",
            {
                "pane_id": pane_id,
                "source": "recent",
                "match": {"type": "regex", "value": pattern},
                "timeout_ms": 10000,
            },
        )
        self.assertEqual(response["type"], "output_matched")

    def _read_pane(self, pane_id):
        response = self.transport(
            "pane.read", {"pane_id": pane_id, "source": "recent"}
        )
        self.assertEqual(response["type"], "pane_read")
        return str(response["read"]["text"])

    def _report_agent(self, pane_id, agent, state):
        response = self.transport(
            "pane.report_agent",
            {
                "pane_id": pane_id,
                "source": "forma-fixture",
                "agent": agent,
                "state": state,
            },
        )
        self.assertEqual(response["type"], "ok")

    def test_two_agents_are_launched_and_detected_by_agent_start(self):
        self._stage("creating isolated panes")
        root = Path(self.temp_root.name)
        dir_a = root / "real-a"
        dir_b = root / "real-b"
        dir_a.mkdir()
        dir_b.mkdir()
        fixture_home = root / "fixture-home"
        fixture_home.mkdir()
        fixture_path = f"{self.fixture_bin}:/usr/bin:/bin"
        (fixture_home / ".bash_profile").write_text(
            f"export PATH={fixture_path!r}\n", encoding="utf-8"
        )
        fixture_env = {"HOME": str(fixture_home), "PATH": fixture_path}
        workspace = self.adapter.open_workspace(
            cwd=str(dir_a), label="forma-real", env=fixture_env
        )
        pane_b = self.adapter.open_pane(
            direction="right",
            target_pane_id=workspace.root_pane_id,
            cwd=str(dir_b),
            env=fixture_env,
        )
        self._send_text(
            workspace.root_pane_id, 'echo "REAL-A-SHELL-READY-$(date +%s)"\n'
        )
        self._send_text(
            pane_b.pane_id, 'echo "REAL-B-SHELL-READY-$(date +%s)"\n'
        )
        self._wait_marker(workspace.root_pane_id, "REAL-A-SHELL-READY-[0-9]+")
        self._wait_marker(pane_b.pane_id, "REAL-B-SHELL-READY-[0-9]+")
        self._stage("both panes ready")

        try:
            task_a = self.adapter.spawn_task(
                task_id="real-a",
                correlation_id="corr-real-a",
                agent_name="fixture-real-a",
                agent_kind="codex",
                pane_id=workspace.root_pane_id,
                startup_timeout_ms=5_000,
            )
        except Exception as exc:
            raise AssertionError(self._read_pane(workspace.root_pane_id)) from exc
        self._stage("agent A detected")
        task_b = self.adapter.spawn_task(
            task_id="real-b",
            correlation_id="corr-real-b",
            agent_name="fixture-real-b",
            agent_kind="codex",
            pane_id=pane_b.pane_id,
            startup_timeout_ms=5_000,
        )
        self._stage("agent B detected")

        self.assertNotEqual(task_a.run_id, task_b.run_id)
        self.assertNotEqual(task_a.pane_id, task_b.pane_id)
        raw_a = self.transport("agent.get", {"target": task_a.pane_id})["agent"]
        raw_b = self.transport("agent.get", {"target": task_b.pane_id})["agent"]
        self.assertEqual(raw_a.get("agent"), "codex", raw_a)
        self.assertEqual(raw_b.get("agent"), "codex", raw_b)
        self.assertEqual(raw_a["name"], "fixture-real-a")
        self.assertEqual(raw_b["name"], "fixture-real-b")
        self.assertTrue(raw_a["interactive_ready"])
        self.assertTrue(raw_b["interactive_ready"])
        self.assertFalse(raw_a.get("launch_pending", False))
        self.assertFalse(raw_b.get("launch_pending", False))
        self.assertNotEqual(raw_a["terminal_id"], raw_b["terminal_id"])

        self._send_text(task_a.pane_id, "fixture-a\n")
        self._send_text(task_b.pane_id, "fixture-b\n")
        self._wait_marker(task_b.pane_id, "FIXTURE-B-DONE-[0-9]+")
        self._stage("parallel completion marker observed")
        running_a = self.adapter.task_status(task_a.run_id)
        cancel = self.adapter.cancel_task(
            run_id=task_a.run_id,
            correlation_id="corr-cancel-real-a",
            expected_revision=running_a.revision,
        )
        self.assertEqual(cancel.action, "graceful_interrupt")
        self._stage("agent A cancellation requested")
        self._send_text(task_a.pane_id, 'echo "REAL-A-BACK-$(date +%s)"\n')
        self._wait_marker(task_a.pane_id, "REAL-A-BACK-[0-9]+")

        a_start = int((dir_a / "a_start.txt").read_text().strip())
        b_end = int((dir_b / "b_end.txt").read_text().strip())
        self.assertLess(b_end - a_start, 8)
        self.assertFalse((dir_a / "a_leak.txt").exists())
        self.assertEqual(
            sorted(path.name for path in dir_a.iterdir()), ["a_start.txt"]
        )
        self.assertEqual(
            sorted(path.name for path in dir_b.iterdir()),
            ["b_end.txt", "b_start.txt"],
        )
        text_a = self._read_pane(task_a.pane_id)
        text_b = self._read_pane(task_b.pane_id)
        self.assertNotIn("FIXTURE-B-DONE", text_a)
        self.assertNotIn("FIXTURE-A-FINISHED", text_b)
        self._stage("isolation assertions complete")

    def test_blocked_agent_wait_read_and_explicit_force_close(self):
        root = Path(self.temp_root.name)
        workdir = root / "blocked"
        workdir.mkdir()
        fixture_home = root / "blocked-home"
        fixture_home.mkdir()
        fixture_path = f"{self.fixture_bin}:/usr/bin:/bin"
        (fixture_home / ".bash_profile").write_text(
            f"export PATH={fixture_path!r}\n", encoding="utf-8"
        )
        workspace = self.adapter.open_workspace(
            cwd=str(workdir),
            label="forma-p3t14-blocked",
            env={"HOME": str(fixture_home), "PATH": fixture_path},
        )
        self._send_text(
            workspace.root_pane_id,
            'echo "P3T14-BLOCKED-READY-$(date +%s)"\n',
        )
        self._wait_marker(
            workspace.root_pane_id,
            "P3T14-BLOCKED-READY-[0-9]+",
        )
        time.sleep(0.75)
        task = self.adapter.spawn_task(
            task_id="blocked",
            correlation_id="corr-blocked",
            agent_name="fixture-blocked",
            agent_kind="codex",
            pane_id=workspace.root_pane_id,
            startup_timeout_ms=5_000,
        )
        prompted = self.transport(
            "agent.prompt",
            {
                "target": task.pane_id,
                "text": "fixture-blocked",
                "wait": {"until": ["blocked"], "timeout_ms": 5_000},
            },
        )
        self.assertEqual(prompted["type"], "agent_prompted")
        self.assertEqual(prompted["agent"]["agent_status"], "blocked")

        blocked = self.adapter.wait_for_task(
            run_id=task.run_id,
            until=("blocked",),
            timeout_ms=1_000,
        )
        self.assertEqual(blocked.state, "blocked")
        output = self.adapter.read_task_output(
            run_id=task.run_id,
            source="recent",
            lines=50,
        )
        self.assertLessEqual(len(output.text.splitlines()), 50)
        self.assertNotIn("\x1b", output.text)
        self.assertIn("Awaiting explicit approval", output.text)
        process = self.adapter.task_process_info(run_id=task.run_id)
        self.assertTrue(process.foreground_process_ids)

        graceful = self.adapter.cancel_task(
            run_id=task.run_id,
            correlation_id="corr-graceful",
            expected_revision=blocked.revision,
        )
        self.assertEqual(graceful.action, "graceful_interrupt")
        forced = self.adapter.force_cancel_task(
            run_id=task.run_id,
            correlation_id="corr-force",
            expected_revision=blocked.revision,
            force_confirmed=True,
        )
        self.assertEqual(forced.action, "force_close")
        self.assertEqual(forced.state, "force_closed")
        with self.assertRaises(HerdrRequestError) as ctx:
            self.transport("agent.get", {"target": task.pane_id})
        self.assertEqual(ctx.exception.code, "agent_not_found")


@unittest.skipUnless(
    _find_herdr_binary(), "verified Herdr artifact binary is not available"
)
class HerdrEventSubscriptionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.binary = _find_herdr_binary()
        self.temp_root = tempfile.TemporaryDirectory(prefix="forma-p3t13-test-")
        self.session_name = f"forma-p3t13-test-{uuid.uuid4().hex[:8]}"
        self.socket_path = os.path.join(
            os.path.expanduser("~"),
            ".config",
            "herdr",
            "sessions",
            self.session_name,
            "herdr.sock",
        )
        self.server = None
        try:
            self._start_server()
            self.transport = HerdrSocketTransport(
                socket_path=self.socket_path, environ={}, request_timeout=60.0
            )
            self.adapter = HerdrAdapter(
                executable_finder=lambda _name: self.binary,
                clock=lambda: "2026-09-01T00:00:00Z",
                request=self.transport,
                probe=self.transport.probe,
            )
        except Exception:
            self.tearDown()
            raise

    def _start_server(self):
        self.server = subprocess.Popen(
                [self.binary, "--session", self.session_name, "server"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        deadline = time.monotonic() + 15.0
        while not os.path.exists(self.socket_path):
            if time.monotonic() > deadline:
                raise AssertionError("Herdr test server socket did not appear")
            if self.server.poll() is not None:
                raise AssertionError(
                    f"Herdr test server exited early with {self.server.returncode}"
                )
            time.sleep(0.1)

    def tearDown(self):
        for args in (
            ["session", "stop", self.session_name, "--json"],
            ["session", "delete", self.session_name, "--json"],
        ):
            subprocess.run(
                [self.binary, *args],
                capture_output=True,
                timeout=30,
            )
        if self.server is not None and self.server.poll() is None:
            self.server.terminate()
            try:
                self.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server.kill()
                self.server.wait(timeout=5)
        if hasattr(self, "temp_root"):
            self.temp_root.cleanup()

    def _report_agent(self, pane_id, agent, state):
        response = self.transport(
            "pane.report_agent",
            {
                "pane_id": pane_id,
                "source": "forma-fixture",
                "agent": agent,
                "state": state,
            },
        )
        self.assertEqual(response["type"], "ok")

    def _subscribe_once(self, listener, pane_id, received, errors):
        def on_event(message):
            received.append(message)
            listener.stop()

        def run():
            try:
                listener.subscribe(
                    [{"type": "pane.agent_status_changed", "pane_id": pane_id}],
                    on_event,
                )
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=run)
        thread.start()
        time.sleep(0.5)
        return thread

    def test_live_transitions_subscription_and_reconnect_resubscribe(self):
        root = Path(self.temp_root.name)
        workspace = self.adapter.open_workspace(cwd=str(root), label="forma-p3t13")
        pane_id = workspace.root_pane_id
        self._report_agent(pane_id, "fixture-sub-a", "working")

        snapshot = self.adapter.snapshot()
        self.assertEqual(snapshot.protocol, 20)
        agent = next(item for item in snapshot.agents if item.pane_id == pane_id)
        self.assertEqual(agent.agent_status, "working")

        listener = HerdrSubscriptionListener(
            socket_path=self.socket_path, environ={}
        )
        received = []
        errors = []
        thread = self._subscribe_once(listener, pane_id, received, errors)
        self._report_agent(pane_id, "fixture-sub-a", "blocked")
        thread.join(timeout=10.0)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["event"], "pane.agent_status_changed")
        self.assertEqual(received[0]["data"]["pane_id"], pane_id)
        self.assertEqual(received[0]["data"]["agent_status"], "blocked")

        self._report_agent(pane_id, "fixture-sub-a", "idle")
        # events.wait matches the pane's current state, not an event history:
        # the idle transition fired with no subscription attached, yet the
        # wait still returns it immediately.
        matched = self.adapter.wait_for_event(
            match_event={
                "event": "pane_agent_status_changed",
                "pane_id": pane_id,
                "agent_status": "idle",
            },
            timeout_ms=2000,
        )
        self.assertEqual(matched.data["agent_status"], "idle")
        # A state that was never set never matches and fails closed on timeout.
        with self.assertRaises(HerdrRequestError) as ctx:
            self.adapter.wait_for_event(
                match_event={
                    "event": "pane_agent_status_changed",
                    "pane_id": pane_id,
                    "agent_status": "unknown",
                },
                timeout_ms=1000,
            )
        self.assertEqual(ctx.exception.code, "timeout")

        reconciled = self.adapter.snapshot()
        reconciled_agent = next(
            item for item in reconciled.agents if item.pane_id == pane_id
        )
        self.assertEqual(reconciled_agent.agent_status, "idle")

        raw_reconnected_events = []

        class StopAfterEventListener(HerdrSubscriptionListener):
            def subscribe(inner_self, subscriptions, on_event):
                def receive(message):
                    raw_reconnected_events.append(message)
                    on_event(message)
                    inner_self.stop()

                return super(StopAfterEventListener, inner_self).subscribe(
                    subscriptions, receive
                )

        provider = HerdrPresentationProvider(
            adapter=self.adapter,
            listener_factory=lambda: StopAfterEventListener(
                socket_path=self.socket_path, environ={}
            ),
        )
        updates = []
        errors_again = []
        recovered_panes = []

        def update(item):
            updates.append(item)
            if item.freshness == "stale":
                self._start_server()
                recovered = self.adapter.open_workspace(
                    cwd=str(root), label="forma-p3t13-recovered"
                )
                self._report_agent(
                    recovered.root_pane_id, "fixture-sub-recovered", "idle"
                )
                recovered_panes.append(recovered.root_pane_id)

        def run_provider():
            try:
                provider.run_reconnecting(update, maximum_reconnects=1)
            except Exception as exc:
                errors_again.append(exc)

        thread_again = threading.Thread(target=run_provider)
        thread_again.start()
        deadline = time.monotonic() + 5.0
        while len(updates) < 1 and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertEqual(updates[0].freshness, "fresh")
        time.sleep(0.5)

        # Kill the server-side socket owner, not the listener itself. The
        # provider must invalidate its projection before its callback restarts
        # the same named Herdr session.
        self.server.terminate()
        self.server.wait(timeout=5)
        deadline = time.monotonic() + 10.0
        while len(updates) < 3 and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertEqual(updates[1].freshness, "stale")
        self.assertEqual(updates[1].agents[0].state, "unknown")
        self.assertEqual(updates[2].freshness, "fresh")
        self.assertEqual(updates[2].agents[0].state, "idle")
        self.assertEqual(updates[2].agents[0].pane_id, recovered_panes[0])
        self.assertNotEqual(recovered_panes[0], pane_id)

        time.sleep(0.5)
        self._report_agent(
            recovered_panes[0], "fixture-sub-recovered", "working"
        )
        thread_again.join(timeout=10.0)
        self.assertFalse(thread_again.is_alive())
        self.assertEqual(errors_again, [])
        self.assertEqual(updates[-1].freshness, "fresh")
        self.assertEqual(
            updates[-1].agents[0].state,
            "working",
            msg=repr(raw_reconnected_events),
        )


if __name__ == "__main__":
    unittest.main()
