import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "process-memory-secret-with-at-least-32-characters"


class MemoryServiceProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.product_root = Path(self.temp.name) / "Product"
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            self.port = probe.getsockname()[1]
        self.process = None

    def tearDown(self):
        self.stop()
        self.temp.cleanup()

    def start(self):
        self.process = subprocess.Popen(
            [
                sys.executable, str(ROOT / "scripts/supervisor.py"),
                "--request-id", str(uuid.uuid4()), "internal-memory-service",
                "--root", str(self.product_root), "--memory-port", str(self.port),
            ],
            cwd=ROOT,
            env={
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "HOME": str(self.product_root / "state/homes/memory-test"),
                "TMPDIR": str(self.product_root / "state/runtime/memory-test/tmp"),
                "FORMA_AI_MEMORY_TOKEN": TOKEN,
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=1)
                self.fail(f"memory process exited early: {stdout!r} {stderr!r}")
            try:
                if self.request("GET", "/live")[0] == 200:
                    return
            except (OSError, urllib.error.URLError):
                time.sleep(0.05)
        self.fail("memory process did not become live")

    def stop(self):
        process = self.process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if process is not None:
            process.communicate(timeout=1)
        self.process = None

    def request(self, method, path, payload=None, correlation="process-memory-1"):
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "X-Correlation-ID": correlation,
            "Accept": "application/json",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=1) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_real_process_is_live_unavailable_and_preserves_candidate_across_restart(self):
        self.start()
        status, health = self.request("GET", "/v1/memory/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["result"]["status"], "unavailable")
        self.assertEqual(
            health["result"]["semantica"]["code"], "EMBEDDING_ROUTE_UNVERIFIED"
        )
        source = {"uri": "fixture://process/1", "observed_at": "2026-08-30T00:00:00+00:00"}
        status, proposed = self.request("POST", "/v1/memory/propose", {
            "actor": "process-user", "claim_key": "process.fact",
            "content": "Candidate survives restart", "sources": [source],
        })
        self.assertEqual(status, 200)
        candidate = proposed["result"]["candidate_id"]
        self.stop()
        self.start()
        status, denied = self.request("POST", "/v1/memory/confirm", {
            "actor": "process-reviewer", "candidate_id": candidate,
        }, correlation="process-memory-2")
        self.assertEqual(status, 503)
        self.assertEqual(denied["error"]["code"], "SEMANTICA_UNAVAILABLE")
        audit = self.product_root / "logs/audit/memory-service.jsonl"
        self.assertIn("process-memory-2", audit.read_text(encoding="utf-8"))
        self.assertNotIn("Candidate survives restart", audit.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
