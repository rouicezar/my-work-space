"""Live two-fixture-agent isolation proof against the verified Herdr binary."""

import os
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.herdr_transport import HerdrSocketTransport


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


if __name__ == "__main__":
    unittest.main()
