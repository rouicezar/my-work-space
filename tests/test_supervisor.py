import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from scripts import preflight, supervisor


ROOT = Path(__file__).resolve().parents[1]


class SupervisorProtocolTests(unittest.TestCase):
    def test_preflight_wraps_authoritative_report_and_correlation(self):
        request_id = str(uuid.uuid4())
        expected = {"schema_version": 1, "status": "supported"}
        args = supervisor.parser().parse_args(
            ["--request-id", request_id, "preflight", "--check-path", str(ROOT)]
        )
        with patch.object(preflight, "build_report", return_value=expected) as build:
            response = supervisor.run(args)
        self.assertEqual(response["schema_version"], 1)
        self.assertEqual(response["command"], "preflight")
        self.assertEqual(response["request_id"], request_id)
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["payload"], expected)
        self.assertIsNone(response["error"])
        build.assert_called_once()

    def test_invalid_request_id_returns_structured_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/supervisor.py",
                    "--request-id",
                    "not-a-uuid",
                    "preflight",
                    "--check-path",
                    directory,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        response = json.loads(result.stdout)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"]["code"], "SUPERVISOR_COMMAND_FAILED")
        self.assertNotIn("not-a-uuid", response["error"]["message"])
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_command_is_a_structured_protocol_error(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/supervisor.py",
                "--request-id",
                str(uuid.uuid4()),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        response = json.loads(result.stdout)
        self.assertEqual(response["command"], "unknown")
        self.assertEqual(response["status"], "error")
        self.assertEqual(result.stderr, "")

    def test_relative_paths_and_invalid_ports_fail_before_probe(self):
        request_id = str(uuid.uuid4())
        for extra in (
            ["--profiles", "relative.json", "--check-path", str(ROOT)],
            ["--profiles", str(ROOT / "config/hardware-profiles.yaml"), "--check-path", "relative"],
            ["--check-path", str(ROOT), "--ports", "80"],
            ["--check-path", str(ROOT), "--ports", "8000", "8000"],
        ):
            with self.subTest(extra=extra):
                args = supervisor.parser().parse_args(
                    ["--request-id", request_id, "preflight", *extra]
                )
                with self.assertRaises(ValueError):
                    supervisor.run(args)


if __name__ == "__main__":
    unittest.main()
