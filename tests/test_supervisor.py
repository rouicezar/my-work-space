import json
import subprocess
import sys
import tempfile
import unittest
import uuid
import hashlib
from pathlib import Path
from unittest.mock import patch

from scripts import preflight, supervisor
from mac_ai_work_os.installer import ActiveBundle


ROOT = Path(__file__).resolve().parents[1]


class SupervisorProtocolTests(unittest.TestCase):
    def write_upstreams(self, directory: Path) -> Path:
        manifest = directory / "upstreams.json"
        payload = b"fixture"
        manifest.write_text(json.dumps({
            "components": [{
                "id": "omlx", "release": "v1.2.3", "artifacts": [{
                    "id": "macos", "name": "omlx.dmg", "platform": "macos",
                    "minimum_macos_major": 15, "maximum_macos_major": 99,
                    "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                    "url": "https://github.com/example/omlx.dmg"
                }]
            }]
        }), encoding="utf-8")
        return manifest

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

    def test_installation_plan_is_exact_and_does_not_begin_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            upstreams = self.write_upstreams(base)
            partial = root / "cache/downloads/omlx.dmg.part"
            partial.parent.mkdir(parents=True)
            partial.write_bytes(b"fix")
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "installation-plan",
                "--root", str(root), "--os-major", "26", "--upstreams", str(upstreams),
            ])
            response = supervisor.run(args)
            payload = response["payload"]
            self.assertEqual(payload["artifact_size_bytes"], 7)
            self.assertEqual(payload["downloaded_bytes"], 3)
            self.assertTrue(payload["approval_required"])
            self.assertFalse((root / "state/operations/omlx-install/operation.json").exists())

    def test_installation_plan_does_not_trust_stale_active_record(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            upstreams = self.write_upstreams(base)
            record = root / "state/components/omlx-active.json"
            record.parent.mkdir(parents=True)
            record.write_text(json.dumps({
                "schema_version": 1, "component": "omlx", "release": "v1.2.3",
                "artifact_sha256": hashlib.sha256(b"fixture").hexdigest(),
                "app_path": str(root / "runtimes/omlx/v1.2.3/oMLX.app")
            }), encoding="utf-8")
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "installation-plan", "--root", str(root),
                "--os-major", "26", "--upstreams", str(upstreams),
            ])
            self.assertFalse(supervisor.run(args)["payload"]["already_active"])

    def test_installation_status_reports_absence_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "installation-status", "--root", str(root),
            ])
            response = supervisor.run(args)
            self.assertIsNone(response["payload"]["operation"])
            self.assertFalse(root.exists())

    def test_install_requires_exact_artifact_approval_and_delegates(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            upstreams = self.write_upstreams(base)
            digest = hashlib.sha256(b"fixture").hexdigest()
            common = ["--request-id", str(uuid.uuid4()), "install-omlx", "--root", str(root),
                      "--os-major", "26", "--upstreams", str(upstreams)]
            mismatch = supervisor.parser().parse_args([*common, "--approve-artifact-sha256", "0" * 64])
            with self.assertRaises(ValueError):
                supervisor.run(mismatch)
            active = ActiveBundle(1, "omlx", "v1.2.3", digest, "/Product/oMLX.app", "app.omlx", "1.2.3", "now")
            approved = supervisor.parser().parse_args([*common, "--approve-artifact-sha256", digest])
            with patch.object(supervisor.OMLXInstaller, "run", return_value=active) as run:
                response = supervisor.run(approved)
            run.assert_called_once_with()
            self.assertEqual(response["payload"]["active"]["release"], "v1.2.3")

    def test_installation_commands_reject_relative_home_and_root_paths(self):
        request = str(uuid.uuid4())
        for root in ("relative", "/", str(Path.home())):
            with self.subTest(root=root):
                args = supervisor.parser().parse_args([
                    "--request-id", request, "installation-status", "--root", root,
                ])
                with self.assertRaises(ValueError):
                    supervisor.run(args)

    def test_installer_runtime_failure_is_structured_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            upstreams = self.write_upstreams(base)
            digest = hashlib.sha256(b"fixture").hexdigest()
            with patch.object(supervisor.OMLXInstaller, "run", side_effect=RuntimeError("secret detail")):
                with patch.object(sys, "argv", [
                    "supervisor.py", "--request-id", str(uuid.uuid4()), "install-omlx",
                    "--root", str(base / "Product"), "--os-major", "26",
                    "--upstreams", str(upstreams), "--approve-artifact-sha256", digest,
                ]):
                    with patch("builtins.print") as output:
                        self.assertEqual(supervisor.main(), 2)
            response = json.loads(output.call_args.args[0])
            self.assertEqual(response["error"]["code"], "SUPERVISOR_COMMAND_FAILED")
            self.assertNotIn("secret detail", response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
