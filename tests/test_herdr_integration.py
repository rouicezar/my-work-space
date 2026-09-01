"""Live Herdr integration proofs against the verified Herdr binary."""

import os
import subprocess
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path

from forma_ai.herdr_adapter import HerdrAdapter
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
    def setUp(self):
        self.binary = _find_herdr_binary()
        self.session_name = f"forma-p3t12-test-{uuid.uuid4().hex[:8]}"
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
                "timeout_ms": 20000,
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

    def test_two_fixture_agents_run_in_parallel_without_leakage(self):
        root = Path(tempfile.mkdtemp(prefix="forma-p3t12-test-"))
        dir_a = root / "a"
        dir_b = root / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        workspace = self.adapter.open_workspace(cwd=str(dir_a), label="forma-p3t12")
        pane_a_id = workspace.root_pane_id
        pane_b = self.adapter.open_pane(
            direction="right",
            target_pane_id=pane_a_id,
            cwd=str(dir_b),
        )

        self.assertNotEqual(pane_b.pane_id, pane_a_id)
        self.assertEqual(pane_b.workspace_id, workspace.workspace_id)

        self._send_text(pane_a_id, 'echo "A-READY-$(date +%s)"\n')
        self._send_text(pane_b.pane_id, 'echo "B-READY-$(date +%s)"\n')
        self._wait_marker(pane_a_id, "A-READY-[0-9]+")
        self._wait_marker(pane_b.pane_id, "B-READY-[0-9]+")

        task_a = self.adapter.spawn_reported_task(
            task_id="fixture-a",
            correlation_id="corr-a",
            agent_name="fixture-agent-a",
            pane_id=pane_a_id,
            command=(
                "date +%s > a_start.txt; sleep 8; "
                'echo A-LEAK > a_leak.txt; echo "A-FINISHED-$(date +%s)"\n'
            ),
        )
        task_b = self.adapter.spawn_reported_task(
            task_id="fixture-b",
            correlation_id="corr-b",
            agent_name="fixture-agent-b",
            pane_id=pane_b.pane_id,
            command=(
                "date +%s > b_start.txt; sleep 2.5; "
                'date +%s > b_end.txt; echo "B-DONE-$(date +%s)"\n'
            ),
        )

        self.assertNotEqual(task_a.run_id, task_b.run_id)
        self.assertNotEqual(task_a.pane_id, task_b.pane_id)

        running_a = self.adapter.task_status(task_a.run_id)
        self.assertEqual(running_a.state, "running")

        self._wait_marker(pane_b.pane_id, "B-DONE-[0-9]+")
        self._report_agent(pane_b.pane_id, "fixture-agent-b", "idle")

        cancel = self.adapter.cancel_task(
            run_id=task_a.run_id,
            correlation_id="corr-cancel-a",
            expected_revision=running_a.revision,
        )
        self.assertEqual(cancel.action, "graceful_interrupt")
        self._send_text(pane_a_id, 'echo "A-BACK-$(date +%s)"\n')
        self._wait_marker(pane_a_id, "A-BACK-[0-9]+")
        self._report_agent(pane_a_id, "fixture-agent-a", "idle")

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

        text_a = self._read_pane(pane_a_id)
        text_b = self._read_pane(pane_b.pane_id)
        self.assertRegex(text_a, "A-BACK-[0-9]+")
        self.assertNotRegex(text_a, "A-FINISHED-[0-9]+")
        self.assertNotIn("B-DONE", text_a)
        self.assertRegex(text_b, "B-DONE-[0-9]+")
        self.assertNotIn("A-READY", text_b)
        self.assertNotIn("A-LEAK", text_b)

        snapshot_response = self.transport("session.snapshot", {})
        snapshot = snapshot_response["snapshot"]
        agents = {agent["agent"]: agent for agent in snapshot["agents"]}
        self.assertEqual(set(agents), {"fixture-agent-a", "fixture-agent-b"})
        self.assertEqual(agents["fixture-agent-a"]["agent_status"], "idle")
        self.assertEqual(agents["fixture-agent-b"]["agent_status"], "idle")
        self.assertNotEqual(
            agents["fixture-agent-a"]["pane_id"],
            agents["fixture-agent-b"]["pane_id"],
        )


@unittest.skipUnless(
    _find_herdr_binary(), "verified Herdr artifact binary is not available"
)
class HerdrEventSubscriptionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.binary = _find_herdr_binary()
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
        root = Path(tempfile.mkdtemp(prefix="forma-p3t13-test-"))
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

        received_again = []
        errors_again = []
        thread_again = self._subscribe_once(
            listener, pane_id, received_again, errors_again
        )
        self._report_agent(pane_id, "fixture-sub-a", "working")
        thread_again.join(timeout=10.0)
        self.assertFalse(thread_again.is_alive())
        self.assertEqual(errors_again, [])
        self.assertEqual(len(received_again), 1)
        self.assertEqual(received_again[0]["data"]["agent_status"], "working")


if __name__ == "__main__":
    unittest.main()
