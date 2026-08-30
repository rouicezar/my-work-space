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
from mac_ai_work_os.models import ModelDefinition, ModelFile, ModelReference
from mac_ai_work_os.semantica_runtime import SemanticaRuntimeInspector


ROOT = Path(__file__).resolve().parents[1]


class SupervisorProtocolTests(unittest.TestCase):
    def model(self):
        return ModelDefinition(
            id="fixture-model", repository="test/model", revision="a" * 40,
            license="Apache-2.0", license_url="https://example.test/license",
            model_type="fixture", architecture="Fixture", capabilities=("chat",), quantization_bits=4,
            files={"weights.bin": ModelFile(10, "b" * 64)},
        )
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
            self.assertFalse(payload["cached_artifact_verified"])
            self.assertIsNone(payload["cache_blocker"])
            self.assertTrue(payload["approval_required"])
            self.assertFalse((root / "state/operations/omlx-install/operation.json").exists())

    def test_installation_plan_blocks_unverified_complete_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            upstreams = self.write_upstreams(base)
            cached = root / "cache/downloads/omlx.dmg"
            cached.parent.mkdir(parents=True)
            cached.write_bytes(b"invalid")
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "installation-plan", "--root", str(root),
                "--os-major", "26", "--upstreams", str(upstreams),
            ])
            payload = supervisor.run(args)["payload"]
            self.assertFalse(payload["cached_artifact_verified"])
            self.assertEqual(payload["cache_blocker"], "DESTINATION_INVALID")
            self.assertEqual(payload["downloaded_bytes"], 0)

    def test_installation_plan_reuses_only_verified_complete_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            upstreams = self.write_upstreams(base)
            cached = root / "cache/downloads/omlx.dmg"
            cached.parent.mkdir(parents=True)
            cached.write_bytes(b"fixture")
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "installation-plan", "--root", str(root),
                "--os-major", "26", "--upstreams", str(upstreams),
            ])
            payload = supervisor.run(args)["payload"]
            self.assertTrue(payload["cached_artifact_verified"])
            self.assertIsNone(payload["cache_blocker"])
            self.assertEqual(payload["downloaded_bytes"], 7)

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

    def test_installation_plan_recognizes_matching_active_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            upstreams = self.write_upstreams(base)
            app = root / "runtimes/omlx/v1.2.3/oMLX.app"
            app.mkdir(parents=True)
            record = root / "state/components/omlx-active.json"
            record.parent.mkdir(parents=True)
            record.write_text(json.dumps({
                "schema_version": 1, "component": "omlx", "release": "v1.2.3",
                "artifact_sha256": hashlib.sha256(b"fixture").hexdigest(),
                "app_path": str(app)
            }), encoding="utf-8")
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "installation-plan", "--root", str(root),
                "--os-major", "26", "--upstreams", str(upstreams),
            ])
            self.assertTrue(supervisor.run(args)["payload"]["already_active"])

    def test_installation_status_reports_absence_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "installation-status", "--root", str(root),
            ])
            response = supervisor.run(args)
            self.assertIsNone(response["payload"]["operation"])
        self.assertFalse(root.exists())

    def test_semantica_status_is_correlated_read_only_and_honest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "semantica-status", "--root", str(root),
            ])
            response = supervisor.run(args)
            self.assertEqual(response["command"], "semantica-status")
            self.assertEqual(response["payload"]["installation"], "not_installed")
            self.assertEqual(response["payload"]["code"], "SEMANTICA_NOT_INSTALLED")
            self.assertFalse(root.exists())

    def test_semantica_status_delegates_to_runtime_inspector(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            expected = {"schema_version": 1, "status": "unavailable", "code": "fixture"}
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "semantica-status", "--root", str(root),
            ])
            with patch.object(SemanticaRuntimeInspector, "status", return_value=expected) as status:
                response = supervisor.run(args)
            status.assert_called_once_with()
            self.assertEqual(response["payload"], expected)

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

    def test_model_plan_verifies_existing_cache_without_linking(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            catalog = base / "models.json"
            catalog.write_text("{}", encoding="utf-8")
            cache = base / "cache"
            cache.mkdir()
            snapshot = cache / "snapshot"
            snapshot.mkdir()
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "model-plan", "--root", str(base / "Product"),
                "--cache-root", str(cache), "--catalog", str(catalog), "--model-id", "fixture-model",
            ])
            with patch.object(supervisor, "load_model", return_value=self.model()), \
                 patch.object(supervisor, "huggingface_snapshot", return_value=snapshot), \
                 patch.object(supervisor, "verify_snapshot", return_value=snapshot):
                response = supervisor.run(args)
            self.assertTrue(response["payload"]["available_verified"])
            self.assertEqual(response["payload"]["size_bytes"], 10)
            self.assertEqual(response["payload"]["capabilities"], ["chat"])
            self.assertFalse((base / "Product").exists())

    def test_model_plan_reports_missing_as_data_not_false_success(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            catalog = base / "models.json"
            catalog.write_text("{}", encoding="utf-8")
            cache = base / "cache"
            cache.mkdir()
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "model-plan", "--root", str(base / "Product"),
                "--cache-root", str(cache), "--catalog", str(catalog),
            ])
            failure = RuntimeError("missing")
            failure.code = "SNAPSHOT_MISSING"
            with patch.object(supervisor, "load_model", return_value=self.model()), \
                 patch.object(supervisor, "verify_snapshot", side_effect=failure):
                response = supervisor.run(args)
            self.assertFalse(response["payload"]["available_verified"])
            self.assertEqual(response["payload"]["unavailable_reason"], "SNAPSHOT_MISSING")

    def test_model_link_requires_revision_approval_and_delegates(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            catalog = base / "models.json"
            catalog.write_text("{}", encoding="utf-8")
            cache = base / "cache"
            cache.mkdir()
            common = ["--request-id", str(uuid.uuid4()), "link-model", "--root", str(base / "Product"),
                      "--cache-root", str(cache), "--catalog", str(catalog)]
            with patch.object(supervisor, "load_model", return_value=self.model()):
                with self.assertRaises(ValueError):
                    supervisor.run(supervisor.parser().parse_args([*common, "--approve-revision", "c" * 40]))
                reference = ModelReference(1, "fixture-model", "test/model", "a" * 40,
                                           str(cache / "snapshot"), str(base / "Product/model"),
                                           "external-reference", "external-cache-not-product-owned", "now")
                with patch.object(supervisor, "link_external_model", return_value=reference) as link:
                    response = supervisor.run(supervisor.parser().parse_args([
                        *common, "--approve-revision", "a" * 40]))
            link.assert_called_once()
            self.assertEqual(response["payload"]["reference"]["storage_mode"], "external-reference")

    def test_runtime_commands_require_distinct_environment_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "start-runtime", "--root", str(root),
            ])
            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaisesRegex(ValueError, "runtime secrets"):
                    supervisor.run(args)
            duplicate = "same-secret-value-with-at-least-32-characters"
            with patch.dict("os.environ", {
                "OMLX_API_KEY": duplicate,
                "MAC_AI_WORK_OS_BROKER_TOKEN": duplicate,
                "MAC_AI_WORK_OS_MEMORY_TOKEN": "m" * 40,
            }, clear=True):
                with self.assertRaisesRegex(ValueError, "distinct"):
                    supervisor.run(args)
            with patch.dict("os.environ", {
                "OMLX_API_KEY": "o" * 40,
                "MAC_AI_WORK_OS_BROKER_TOKEN": duplicate,
                "MAC_AI_WORK_OS_MEMORY_TOKEN": duplicate,
            }, clear=True):
                with self.assertRaisesRegex(ValueError, "distinct"):
                    supervisor.run(args)

    def test_runtime_status_delegates_to_single_runtime_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "runtime-status", "--root", str(root),
            ])
            with patch.object(supervisor.RuntimeManager, "status", return_value={
                "phase": "stopped", "record": None, "omlx_alive": False,
                "broker_alive": False, "memory_alive": False,
            }) as status:
                response = supervisor.run(args)
            status.assert_called_once_with()
            self.assertEqual(response["payload"]["phase"], "stopped")

    def test_memory_liveness_probe_reads_versioned_result_envelope(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self, limit):
                return b'{"schema_version":1,"result":{"status":"ok"}}'

        with patch.object(supervisor.urllib.request, "urlopen", return_value=Response()) as open_url:
            self.assertTrue(supervisor._http_ready(43111, "m" * 40, "/live"))
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:43111/live")

    def test_memory_liveness_probe_rejects_unavailable_nested_status(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self, limit):
                return b'{"schema_version":1,"result":{"status":"unavailable"}}'

        with patch.object(supervisor.urllib.request, "urlopen", return_value=Response()):
            self.assertFalse(supervisor._http_ready(43111, "m" * 40, "/live"))

    def test_sample_task_refuses_nonrunning_runtime_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "sample-task", "--root", str(root),
            ])
            with patch.dict("os.environ", {
                "OMLX_API_KEY": "o" * 40,
                "MAC_AI_WORK_OS_BROKER_TOKEN": "b" * 40,
                "MAC_AI_WORK_OS_MEMORY_TOKEN": "m" * 40,
            }, clear=True), patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "stopped"}), \
                 patch.object(supervisor, "_sample_task") as sample:
                with self.assertRaisesRegex(ValueError, "not running"):
                    supervisor.run(args)
            sample.assert_not_called()


if __name__ == "__main__":
    unittest.main()
