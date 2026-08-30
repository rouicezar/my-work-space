import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mac_ai_work_os.runtime import (
    ProcessRecord, RuntimeManager, RuntimeManagerError, SubprocessController,
)


class FakeController:
    def __init__(self):
        self.next_pid = 100
        self.alive = {}
        self.spawned = []
        self.terminated = []

    def spawn(self, *, role, executable, arguments, environment, working_directory, log_path):
        self.next_pid += 1
        record = ProcessRecord(
            role, self.next_pid, str(executable), "d" * 64,
            f"start-{self.next_pid}", str(log_path),
        )
        self.alive[record.pid] = True
        self.spawned.append((record, tuple(arguments), dict(environment)))
        return record

    def matches(self, record):
        return self.alive.get(record.pid, False)

    def terminate(self, record, timeout):
        if not self.matches(record):
            raise RuntimeManagerError("PID_IDENTITY_MISMATCH", record.role)
        self.alive[record.pid] = False
        self.terminated.append(record.role)

    def adopt(self, *, role, pid, command_prefix, log_path):
        record = ProcessRecord(role, pid, command_prefix, "e" * 64, f"start-{pid}", str(log_path))
        self.alive[pid] = True
        return record


def service(root, name, secret):
    return {
        "executable": root / name,
        "arguments": ["serve", "--port", "8000"],
        "environment": {"PATH": "/usr/bin:/bin", "SECRET": secret},
        "working_directory": root / "work" / name,
        "log_path": root / "logs" / f"{name}.log",
    }


class RuntimeManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Product"
        self.controller = FakeController()
        self.manager = RuntimeManager(self.root, controller=self.controller, wait_interval=0)

    def tearDown(self):
        self.temp.cleanup()

    def test_start_orders_services_persists_redacted_state_and_is_idempotent(self):
        record = self.manager.start(
            correlation_id="request-1",
            omlx=service(self.root, "omlx", "upstream-secret"),
            broker=service(self.root, "broker", "caller-secret"),
            memory=service(self.root, "memory", "memory-secret"),
            omlx_probe=lambda: True,
            broker_probe=lambda: True,
            memory_probe=lambda: True,
        )
        self.assertEqual(record.phase, "running")
        self.assertEqual([item[0].role for item in self.controller.spawned], ["omlx", "broker", "memory"])
        raw = self.manager.state_path.read_text(encoding="utf-8")
        self.assertNotIn("upstream-secret", raw)
        self.assertNotIn("caller-secret", raw)
        self.assertEqual(self.manager.state_path.stat().st_mode & 0o777, 0o600)
        again = self.manager.start(
            correlation_id="request-2",
            omlx=service(self.root, "omlx", "different"),
            broker=service(self.root, "broker", "different"),
            memory=service(self.root, "memory", "different-memory"),
            omlx_probe=lambda: True,
            broker_probe=lambda: True,
            memory_probe=lambda: True,
        )
        self.assertEqual(again.correlation_id, "request-1")
        self.assertEqual(len(self.controller.spawned), 3)

    def test_broker_failure_stops_omlx_and_records_failure_without_secret(self):
        with self.assertRaises(RuntimeManagerError) as failed:
            self.manager.start(
                correlation_id="request-1",
                omlx=service(self.root, "omlx", "upstream-secret"),
                broker=service(self.root, "broker", "caller-secret"),
                memory=service(self.root, "memory", "memory-secret"),
                omlx_probe=lambda: True,
                broker_probe=lambda: False,
                memory_probe=lambda: True,
                timeout=0.001,
            )
        self.assertEqual(failed.exception.code, "BROKER_START_TIMEOUT")
        self.assertEqual(self.controller.terminated, ["broker", "omlx"])
        self.assertEqual(self.manager.load_optional().phase, "failed")
        self.assertNotIn("upstream-secret", self.manager.state_path.read_text(encoding="utf-8"))

    def test_status_degrades_when_recorded_process_identity_no_longer_matches(self):
        record = self.manager.start(
            correlation_id="request-1",
            omlx=service(self.root, "omlx", "a"),
            broker=service(self.root, "broker", "b"),
            memory=service(self.root, "memory", "c"),
            omlx_probe=lambda: True,
            broker_probe=lambda: True,
            memory_probe=lambda: True,
        )
        self.controller.alive[record.broker.pid] = False
        status = self.manager.status()
        self.assertEqual(status["phase"], "degraded")
        self.assertTrue(status["omlx_alive"])
        self.assertFalse(status["broker_alive"])

    def test_real_controller_identity_uses_observed_command_digest_not_launcher_path(self):
        observed = "/resolved/python /Product/supervisor.py internal-broker"
        record = ProcessRecord(
            "broker", 123, "/different/launcher/python3",
            hashlib.sha256(observed.encode()).hexdigest(), "start", "/tmp/broker.log",
        )
        controller = SubprocessController()
        with patch.object(controller, "_process_started_at", return_value="start"), \
             patch.object(controller, "_process_command", return_value=observed):
            self.assertTrue(controller.matches(record))
        with patch.object(controller, "_process_started_at", return_value="start"), \
             patch.object(controller, "_process_command", return_value=observed + " --changed"):
            self.assertFalse(controller.matches(record))

    def test_stop_orders_broker_before_omlx_and_is_idempotent(self):
        self.manager.start(
            correlation_id="request-1",
            omlx=service(self.root, "omlx", "a"),
            broker=service(self.root, "broker", "b"),
            memory=service(self.root, "memory", "c"),
            omlx_probe=lambda: True,
            broker_probe=lambda: True,
            memory_probe=lambda: True,
        )
        stopped = self.manager.stop()
        self.assertEqual(stopped.phase, "stopped")
        self.assertEqual(self.controller.terminated, ["memory", "broker", "omlx"])
        self.manager.stop()
        self.assertEqual(self.controller.terminated, ["memory", "broker", "omlx"])

    def test_start_refuses_live_process_from_incomplete_record(self):
        first = self.manager.start(
            correlation_id="request-1",
            omlx=service(self.root, "omlx", "a"),
            broker=service(self.root, "broker", "b"),
            memory=service(self.root, "memory", "c"),
            omlx_probe=lambda: True,
            broker_probe=lambda: True,
            memory_probe=lambda: True,
        )
        self.controller.alive[first.broker.pid] = False
        with self.assertRaises(RuntimeManagerError) as failed:
            self.manager.start(
                correlation_id="request-2",
                omlx=service(self.root, "omlx", "a"),
                broker=service(self.root, "broker", "b"),
                memory=service(self.root, "memory", "c"),
                omlx_probe=lambda: True,
                broker_probe=lambda: True,
                memory_probe=lambda: True,
            )
        self.assertEqual(failed.exception.code, "RUNTIME_RECOVERY_REQUIRED")

    def test_adopts_real_omlx_server_identity_after_launcher_exits(self):
        adopted = self.controller.adopt(
            role="omlx", pid=999, command_prefix="omlx-server",
            log_path=self.root / "logs/omlx/server.log",
        )
        record = self.manager.start(
            correlation_id="request-1",
            omlx=service(self.root, "omlx-cli", "a"),
            broker=service(self.root, "broker", "b"),
            memory=service(self.root, "memory", "c"),
            omlx_probe=lambda: True,
            broker_probe=lambda: True,
            memory_probe=lambda: True,
            omlx_adopt=lambda: adopted,
        )
        self.assertEqual(record.omlx.pid, 999)
        self.assertEqual(record.omlx.executable, "omlx-server")
        self.controller.alive[self.controller.spawned[0][0].pid] = False
        self.assertEqual(self.manager.status()["phase"], "running")
        self.manager.stop()
        self.assertEqual(self.controller.terminated[-3:], ["memory", "broker", "omlx"])

    def test_memory_failure_stops_all_services_and_records_explicit_code(self):
        with self.assertRaises(RuntimeManagerError) as failed:
            self.manager.start(
                correlation_id="request-memory-failure",
                omlx=service(self.root, "omlx", "a"),
                broker=service(self.root, "broker", "b"),
                memory=service(self.root, "memory", "c"),
                omlx_probe=lambda: True,
                broker_probe=lambda: True,
                memory_probe=lambda: False,
                timeout=0.001,
            )
        self.assertEqual(failed.exception.code, "MEMORY_START_TIMEOUT")
        self.assertEqual(self.controller.terminated, ["memory", "broker", "omlx"])


if __name__ == "__main__":
    unittest.main()
