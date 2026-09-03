"""Live Herdr tool-bridge integration proofs against the verified Herdr binary."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.herdr_transport import HerdrSocketTransport
from forma_ai.tool_registry import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


def _find_herdr_binary() -> str | None:
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
class HerdrToolBridgeIntegrationTests(unittest.TestCase):
    PROOF_ID = "P6-T06"
    WATCHDOG_SECONDS = 60.0

    def _stage(self, name: str) -> None:
        self.current_stage = name
        elapsed = time.monotonic() - self.started_at
        print(
            f"[{self.PROOF_ID} {self.session_name}] {elapsed:05.1f}s {name}",
            file=sys.stderr,
            flush=True,
        )

    def _server_log_tail(self, lines: int = 40) -> str:
        path = getattr(self, "server_output_path", None)
        if path is None or not path.exists():
            return "server output unavailable"
        text = path.read_text(encoding="utf-8", errors="replace")
        return "\n".join(text.splitlines()[-lines:]) or "server output empty"

    def _watchdog_expired(self, _signum, _frame) -> None:
        raise TimeoutError(
            f"{self.PROOF_ID} exceeded {self.WATCHDOG_SECONDS:.0f}s during "
            f"{self.current_stage}\nHerdr server output tail:\n{self._server_log_tail()}"
        )

    def _callTestMethod(self, method):  # noqa: N802
        try:
            return super()._callTestMethod(method)
        except BaseException:
            self._stage(f"failed during {self.current_stage}")
            print(
                f"[{self.PROOF_ID} {self.session_name}] Herdr server output tail:\n"
                f"{self._server_log_tail()}",
                file=sys.stderr,
                flush=True,
            )
            raise

    def setUp(self) -> None:
        self.started_at = time.monotonic()
        self.current_stage = "setup"
        self.binary = _find_herdr_binary()
        self.fixture_bin = Path(__file__).parent / "fixtures" / "herdr_agent_bin"
        proof_slug = self.PROOF_ID.lower().replace("-", "")
        self.temp_root = tempfile.TemporaryDirectory(prefix=f"forma-{proof_slug}-test-")
        self.session_name = f"forma-{proof_slug}-test-{uuid.uuid4().hex[:8]}"
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
        self.product_root = Path(self.temp_root.name) / "Product"
        self.product_root.mkdir()
        ToolRegistry(
            self.product_root,
            catalog_path=ROOT / "config/tool-packages.json",
            repository_root=ROOT,
        ).install("fixture-echo-mcp")
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
                socket_path=self.socket_path, environ={}, request_timeout=30.0
            )
            self.adapter = HerdrAdapter(
                executable_finder=lambda _name: self.binary,
                clock=lambda: "2026-09-03T00:00:00Z",
                request=self.transport,
                probe=self.transport.probe,
            )
        except Exception:
            print(self._server_log_tail(), file=sys.stderr, flush=True)
            self.tearDown()
            raise

    def tearDown(self) -> None:
        cleanup_errors: list[str] = []
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

    def _send_text(self, pane_id: str, text: str) -> None:
        response = self.transport("pane.send_text", {"pane_id": pane_id, "text": text})
        self.assertEqual(response["type"], "ok")

    def _wait_marker(self, pane_id: str, pattern: str) -> None:
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

    def _artifact_files(self, workspace: Path) -> list[Path]:
        directory = workspace / ".forma" / "tool-artifacts"
        if not directory.is_dir():
            return []
        return sorted(directory.glob("*.json"))

    def test_two_tool_calls_execute_via_supervisor_bridge(self) -> None:
        self._stage("creating isolated panes")
        root = Path(self.temp_root.name)
        dir_a = root / "tool-a"
        dir_b = root / "tool-b"
        dir_a.mkdir()
        dir_b.mkdir()
        fixture_home = root / "fixture-home"
        fixture_home.mkdir()
        fixture_path = f"{self.fixture_bin}:/usr/bin:/bin"
        (fixture_home / ".bash_profile").write_text(
            f"export PATH={fixture_path!r}\n", encoding="utf-8"
        )
        fixture_env = {
            "HOME": str(fixture_home),
            "PATH": fixture_path,
            "FORMA_PRODUCT_ROOT": str(self.product_root),
            "FORMA_REPO_ROOT": str(ROOT),
            "FORMA_PYTHON": sys.executable,
        }
        workspace = self.adapter.open_workspace(
            cwd=str(dir_a), label="forma-tool-a", env=fixture_env
        )
        pane_b = self.adapter.open_pane(
            direction="right",
            target_pane_id=workspace.root_pane_id,
            cwd=str(dir_b),
            env=fixture_env,
        )
        self._send_text(
            workspace.root_pane_id, 'echo "TOOL-A-SHELL-READY-$(date +%s)"\n'
        )
        self._send_text(pane_b.pane_id, 'echo "TOOL-B-SHELL-READY-$(date +%s)"\n')
        self._wait_marker(workspace.root_pane_id, "TOOL-A-SHELL-READY-[0-9]+")
        self._wait_marker(pane_b.pane_id, "TOOL-B-SHELL-READY-[0-9]+")
        self._stage("both panes ready")

        task_a = self.adapter.spawn_task(
            task_id="tool-a",
            correlation_id="corr-tool-a",
            agent_name="fixture-tool-a",
            agent_kind="codex",
            pane_id=workspace.root_pane_id,
            startup_timeout_ms=5_000,
        )
        task_b = self.adapter.spawn_task(
            task_id="tool-b",
            correlation_id="corr-tool-b",
            agent_name="fixture-tool-b",
            agent_kind="codex",
            pane_id=pane_b.pane_id,
            startup_timeout_ms=5_000,
        )
        self._stage("both agents detected")

        self._send_text(task_a.pane_id, "fixture-tool-a\n")
        self._send_text(task_b.pane_id, "fixture-tool-b\n")
        self._wait_marker(task_a.pane_id, "FIXTURE-TOOL-A-DONE-[0-9]+")
        self._wait_marker(task_b.pane_id, "FIXTURE-TOOL-B-DONE-[0-9]+")
        self._stage("parallel tool-call markers observed")

        artifacts_a = self._artifact_files(dir_a)
        artifacts_b = self._artifact_files(dir_b)
        self.assertEqual(len(artifacts_a), 1)
        self.assertEqual(len(artifacts_b), 1)
        payload_a = json.loads(artifacts_a[0].read_text(encoding="utf-8"))
        payload_b = json.loads(artifacts_b[0].read_text(encoding="utf-8"))
        self.assertFalse(payload_a["is_error"])
        self.assertFalse(payload_b["is_error"])
        self.assertIn("tool-a", payload_a["text"])
        self.assertIn("tool-b", payload_b["text"])
        self.assertTrue(payload_a["artifact_path"].startswith(".forma/tool-artifacts/"))
        self.assertTrue(payload_b["artifact_path"].startswith(".forma/tool-artifacts/"))
        self.assertTrue((dir_a / "TOOL-A_done.txt").is_file())
        self.assertTrue((dir_b / "TOOL-B_done.txt").is_file())

        audit = self.product_root / "logs/audit/tools.jsonl"
        self.assertTrue(audit.is_file())
        events = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
        self.assertIn("tool_route_proposed", {item["event"] for item in events})
        self.assertIn("tool_call", {item["event"] for item in events})
        self.assertGreaterEqual(sum(item["event"] == "tool_call" for item in events), 2)
        self._stage("tool bridge integration complete")


if __name__ == "__main__":
    unittest.main()
