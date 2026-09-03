import argparse
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts import preflight, supervisor
from forma_ai.installer import ActiveBundle
from forma_ai.models import ModelDefinition, ModelFile, ModelReference
from forma_ai.semantica_runtime import SemanticaRuntimeInspector
from forma_ai.embedding_config import ApprovedEmbeddingRoute
from forma_ai.runtime import RuntimeRecord
from forma_ai.deepseek_adapter import DeepSeekResult, DeepSeekUsage
from forma_ai.local_tasks import LocalTaskError, LocalTaskResult
from forma_ai.cloud_preferences import CloudPreferenceStore
from forma_ai.system_resources import MemoryEvidence
from forma_ai.herdr_adapter import HerdrSessionAgent, HerdrSessionSnapshot
from forma_ai.supervisor import (
    Supervisor,
    SupervisorFeatures,
    SupervisorFeatureUnavailable,
)


ROOT = Path(__file__).resolve().parents[1]


class SupervisorProtocolTests(unittest.TestCase):
    def test_herdr_snapshot_envelope_preserves_authoritative_revision(self):
        expected = HerdrSessionSnapshot(
            version="0.8.2", protocol=20, workspaces=(), tabs=(), panes=(),
            agents=(HerdrSessionAgent(
                terminal_id="terminal-1", agent_status="working",
                workspace_id="workspace-1", tab_id="tab-1", pane_id="pane-1",
                focused=True, revision=9,
            ),), layouts=(),
        )
        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", request_id, "herdr-snapshot",
                "--root", str(root),
            ])
            with patch.object(supervisor.RuntimeManager, "status", return_value={"herdr_alive": True}), \
                 patch.object(supervisor.HerdrAdapter, "snapshot", return_value=expected):
                response = supervisor.run(args)

        self.assertEqual(response["command"], "herdr-snapshot")
        self.assertEqual(response["payload"]["freshness"], "fresh")
        self.assertEqual(response["payload"]["agents"][0]["pane_id"], "pane-1")
        self.assertEqual(response["payload"]["agents"][0]["revision"], 9)

    def test_herdr_snapshot_fails_closed_without_connecting_when_herdr_not_running(self):
        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", request_id, "herdr-snapshot",
                "--root", str(root),
            ])
            with patch.object(supervisor.RuntimeManager, "status", return_value={"herdr_alive": False}), \
                 patch.object(supervisor.HerdrAdapter, "snapshot") as snapshot:
                response = supervisor.run(args)
            snapshot.assert_not_called()

        self.assertEqual(response["payload"]["freshness"], "stale")
        self.assertEqual(response["payload"]["reason"], "HERDR_NOT_RUNNING")
        self.assertEqual(response["payload"]["agents"], [])

    def test_skills_list_returns_catalog_without_injection(self):
        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "excel"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: excel-merge\ndescription: Merge spreadsheets\n---\n# Secret\n",
                encoding="utf-8",
            )
            args = supervisor.parser().parse_args([
                "--request-id", request_id, "skills-list", "--skill-root", str(root),
            ])
            response = supervisor.run(args)
        self.assertEqual(response["command"], "skills-list")
        self.assertEqual(response["payload"]["skills"][0]["name"], "excel-merge")
        self.assertNotIn("Secret", json.dumps(response["payload"]))

    def task_submit_args(self, root: Path, cloud_catalog: Path, request_id: str):
        return supervisor.parser().parse_args([
            "--request-id", request_id, "task-submit", "--root", str(root),
            "--model-catalog", str(ROOT / "config/models.json"),
            "--hardware-profiles", str(ROOT / "config/hardware-profiles.yaml"),
            "--local-profiles", str(ROOT / "config/local-model-profiles.json"),
            "--evidence-root", str(ROOT), "--cloud-catalog", str(cloud_catalog),
        ])

    def task_submit_body(self, *, prompt="短任务", output=32, capabilities=("chat",), classes=("user_text",)):
        return json.dumps({
            "schema_version": 1, "prompt": prompt, "maximum_output_tokens": output,
            "required_capabilities": list(capabilities), "data_classes": list(classes),
        }, ensure_ascii=False).encode()

    def test_task_submit_executes_verified_short_task_locally_without_cloud_proposal(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            request_id = str(uuid.uuid4())
            expected = LocalTaskResult(
                1, "local", request_id, "Qwen3-0.6B-4bit", "result", "stop",
                5, 2, 7, "logs/audit/inference.jsonl",
            )
            with patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "running"}), \
                 patch.object(supervisor, "measure_available_memory", return_value=MemoryEvidence(2048, True, "AVAILABLE_MEMORY_MEASURED")), \
                 patch.object(supervisor, "_runtime_secrets", return_value=("a", "b", "c")), \
                 patch.object(supervisor, "_local_task", return_value=expected) as execute, \
                 patch.object(supervisor, "create_cloud_proposal") as cloud:
                response = supervisor.run(
                    self.task_submit_args(root, catalog, request_id),
                    input_data=self.task_submit_body(),
                )
            self.assertEqual(response["payload"]["plan"]["route"], "local")
            self.assertEqual(response["payload"]["result"]["output"], "result")
            self.assertEqual(execute.call_args.args[4], frozenset({"Qwen3-0.6B-4bit"}))
            cloud.assert_not_called()

    def test_task_submit_creates_offline_proposal_only_when_cloud_is_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            provider = supervisor.load_cloud_provider(catalog, "deepseek")
            CloudPreferenceStore(root).save(
                enabled=True, provider=provider, model_id="deepseek-v4-flash",
                now=datetime.now(timezone.utc),
            )
            request_id = str(uuid.uuid4())
            with patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "stopped"}), \
                 patch.object(supervisor, "measure_available_memory", return_value=MemoryEvidence(2048, True, "AVAILABLE_MEMORY_MEASURED")), \
                 patch.object(supervisor.DeepSeekAdapter, "execute") as network:
                response = supervisor.run(
                    self.task_submit_args(root, catalog, request_id),
                    input_data=self.task_submit_body(capabilities=("tools",)),
                )
            payload = response["payload"]
            self.assertEqual(payload["plan"]["route"], "cloud_proposal_required")
            self.assertIsNone(payload["result"])
            self.assertTrue(payload["proposal"]["proposal_id"])
            network.assert_not_called()

    def test_task_submit_reports_unavailable_when_cloud_is_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            with patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "stopped"}), \
                 patch.object(supervisor, "measure_available_memory", return_value=MemoryEvidence(2048, True, "AVAILABLE_MEMORY_MEASURED")), \
                 patch.object(supervisor, "_local_task") as local, \
                 patch.object(supervisor, "create_cloud_proposal") as cloud:
                response = supervisor.run(
                    self.task_submit_args(root, catalog, str(uuid.uuid4())),
                    input_data=self.task_submit_body(),
                )
            self.assertEqual(response["payload"]["plan"]["route"], "capability_unavailable")
            self.assertIsNone(response["payload"]["proposal"])
            local.assert_not_called()
            cloud.assert_not_called()

    def test_task_submit_turns_cloud_policy_failure_into_honest_unavailable_state(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            provider = supervisor.load_cloud_provider(catalog, "deepseek")
            CloudPreferenceStore(root).save(
                enabled=True, provider=provider, model_id="deepseek-v4-flash",
                now=datetime.now(timezone.utc),
            )
            args = self.task_submit_args(root, catalog, str(uuid.uuid4()))
            with patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "stopped"}), \
                 patch.object(supervisor, "measure_available_memory", return_value=MemoryEvidence(2048, True, "AVAILABLE_MEMORY_MEASURED")):
                response = supervisor.run(
                    args,
                    input_data=self.task_submit_body(
                        capabilities=("tools",), classes=("credentials",),
                    ),
                )
            self.assertEqual(response["payload"]["plan"]["route"], "capability_unavailable")
            self.assertEqual(response["payload"]["cloud_unavailable_code"], "CLOUD_DATA_CLASS_BLOCKED")
            self.assertIsNone(response["payload"]["proposal"])

    def test_task_submit_local_validation_failure_may_create_only_offline_proposal(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            provider = supervisor.load_cloud_provider(catalog, "deepseek")
            CloudPreferenceStore(root).save(
                enabled=True, provider=provider, model_id="deepseek-v4-flash",
                now=datetime.now(timezone.utc),
            )
            with patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "running"}), \
                 patch.object(supervisor, "measure_available_memory", return_value=MemoryEvidence(2048, True, "AVAILABLE_MEMORY_MEASURED")), \
                 patch.object(supervisor, "_runtime_secrets", return_value=("a", "b", "c")), \
                 patch.object(supervisor, "_local_task", side_effect=LocalTaskError("LOCAL_RESPONSE_INVALID", "fixture")), \
                 patch.object(supervisor.DeepSeekAdapter, "execute") as network:
                response = supervisor.run(
                    self.task_submit_args(root, catalog, str(uuid.uuid4())),
                    input_data=self.task_submit_body(),
                )
            self.assertEqual(response["payload"]["plan"]["route"], "cloud_proposal_required")
            self.assertEqual(response["payload"]["plan"]["reason_codes"], ("local_validation_failed",))
            self.assertTrue(response["payload"]["proposal"]["proposal_id"])
            network.assert_not_called()

    def test_task_submit_stale_cloud_price_is_unavailable_not_a_protocol_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            provider = supervisor.load_cloud_provider(catalog, "deepseek")
            CloudPreferenceStore(root).save(
                enabled=True, provider=provider, model_id="deepseek-v4-flash",
                now=datetime.now(timezone.utc),
            )
            raw = json.loads(catalog.read_text(encoding="utf-8"))
            raw["providers"][0]["pricing"]["effective_at"] = "2025-01-01T00:00:00Z"
            catalog.write_text(json.dumps(raw), encoding="utf-8")
            with patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "stopped"}), \
                 patch.object(supervisor, "measure_available_memory", return_value=MemoryEvidence(2048, True, "AVAILABLE_MEMORY_MEASURED")):
                response = supervisor.run(
                    self.task_submit_args(root, catalog, str(uuid.uuid4())),
                    input_data=self.task_submit_body(capabilities=("tools",)),
                )
            self.assertEqual(response["payload"]["plan"]["route"], "capability_unavailable")
            self.assertEqual(response["payload"]["cloud_unavailable_code"], "CLOUD_PRICING_STALE")
            self.assertIsNone(response["payload"]["proposal"])

    def test_cloud_settings_are_default_disabled_and_explicitly_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            common = ["--root", str(root), "--catalog", str(catalog)]
            status = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "cloud-settings", *common,
            ])
            self.assertEqual(supervisor.run(status)["payload"]["code"], "CLOUD_DISABLED_DEFAULT")
            enable = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "set-cloud-settings", *common,
                "--enable", "--model-id", "deepseek-v4-flash",
            ])
            self.assertTrue(supervisor.run(enable)["payload"]["enabled"])
            self.assertEqual(supervisor.run(status)["payload"]["model_id"], "deepseek-v4-flash")
            disable = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "set-cloud-settings", *common, "--disable",
            ])
            self.assertFalse(supervisor.run(disable)["payload"]["enabled"])

    def test_local_task_parses_private_standard_input_and_returns_explicit_route(self):
        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", request_id, "local-task", "--root", str(root),
            ])
            body = json.dumps({
                "schema_version": 1, "prompt": "private local prompt",
                "maximum_output_tokens": 128,
            }).encode()
            expected = LocalTaskResult(
                1, "local", request_id, "qwen", "local result", "stop",
                10, 2, 12, "logs/audit/inference.jsonl",
            )
            with patch.object(supervisor, "_runtime_secrets", return_value=("a", "b", "c")), \
                 patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "running"}), \
                 patch.object(supervisor, "_local_task", return_value=expected) as execute:
                response = supervisor.run(args, input_data=body)
            self.assertEqual(response["payload"]["route"], "local")
            self.assertEqual(response["payload"]["output"], "local result")
            task = execute.call_args.args[3]
            self.assertEqual(task.prompt, "private local prompt")
            self.assertNotIn(
                "private local prompt", " ".join(str(value) for value in vars(args).values()),
            )

    def test_local_task_never_runs_or_proposes_cloud_when_runtime_is_stopped(self):
        with tempfile.TemporaryDirectory() as directory:
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "local-task",
                "--root", str(Path(directory) / "Product"),
            ])
            body = json.dumps({
                "schema_version": 1, "prompt": "x", "maximum_output_tokens": 1,
            }).encode()
            with patch.object(supervisor, "_runtime_secrets", return_value=("a", "b", "c")), \
                 patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "stopped"}), \
                 patch.object(supervisor, "_local_task") as execute, \
                 patch.object(supervisor, "create_cloud_proposal") as cloud:
                with self.assertRaisesRegex(ValueError, "runtime is not running"):
                    supervisor.run(args, input_data=body)
            execute.assert_not_called()
            cloud.assert_not_called()

    def write_current_cloud_catalog(self, directory: Path) -> Path:
        catalog = json.loads((ROOT / "config/cloud-providers.json").read_text(encoding="utf-8"))
        catalog["updated_at"] = datetime.now(timezone.utc).isoformat()
        catalog["providers"][0]["pricing"]["effective_at"] = datetime.now(timezone.utc).isoformat()
        path = directory / "cloud-providers.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        return path

    def cloud_preview_args(self, root: Path, catalog: Path, request_id: str) -> argparse.Namespace:
        return supervisor.parser().parse_args([
            "--request-id", request_id, "cloud-preview", "--root", str(root),
            "--catalog", str(catalog), "--model-id", "deepseek-v4-flash",
            "--estimated-input-tokens", "100", "--maximum-output-tokens", "1000",
            "--minimum-available-memory-mb", "1024", "--required-capability", "chat",
            "--data-class", "user_text", "--reason-code", "local_validation_failed",
        ])

    def test_cloud_preview_approval_and_rejection_are_explicit_and_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            request_id = str(uuid.uuid4())
            prompt = "private fixture text"
            body = json.dumps({
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000, "stream": False,
            }).encode()
            preview = supervisor.run(self.cloud_preview_args(root, catalog, request_id), input_data=body)
            proposal = preview["payload"]["proposal"]
            self.assertTrue(preview["payload"]["approval_required"])
            self.assertNotIn(prompt, json.dumps(preview))
            approve = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "cloud-approve", "--root", str(root),
                "--proposal-id", proposal["proposal_id"], "--maximum-cost-usd",
                str(proposal["estimated_cost"]["maximum"]),
            ])
            approved = supervisor.run(approve)
            self.assertEqual(approved["payload"]["approval"]["proposal_id"], proposal["proposal_id"])
            reject = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "cloud-reject", "--root", str(root),
                "--proposal-id", proposal["proposal_id"],
            ])
            self.assertEqual(supervisor.run(reject)["payload"]["outcome"], "denied")
            self.assertFalse((root / "state/cloud-proposals" / f"{proposal['proposal_id']}.payload").exists())
            audit = (root / "logs/audit/cloud.jsonl").read_text(encoding="utf-8")
            self.assertIn('"outcome":"approved"', audit)
            self.assertIn('"outcome":"denied"', audit)
            self.assertNotIn(prompt, audit)

    def test_cloud_execute_uses_environment_credential_and_removes_pending_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "Product"
            catalog = self.write_current_cloud_catalog(base)
            body = json.dumps({
                "model": "deepseek-v4-flash",
                "messages": [{"role": "user", "content": "fixture"}],
                "max_tokens": 1000, "stream": False,
            }).encode()
            preview = supervisor.run(
                self.cloud_preview_args(root, catalog, str(uuid.uuid4())), input_data=body,
            )["payload"]["proposal"]
            approve = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "cloud-approve", "--root", str(root),
                "--proposal-id", preview["proposal_id"], "--maximum-cost-usd",
                str(preview["estimated_cost"]["maximum"]),
            ])
            supervisor.run(approve)
            execute = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "cloud-execute", "--root", str(root),
                "--proposal-id", preview["proposal_id"], "--catalog", str(catalog),
            ])
            expected = DeepSeekResult(
                "deepseek-v4-flash", "cloud result", "stop", (),
                DeepSeekUsage(10, 0, 10, 2, 12, 0.00001),
            )
            adapter = Mock()
            adapter.execute.return_value = expected
            with patch.object(supervisor, "DeepSeekAdapter", return_value=adapter), \
                 patch.dict(os.environ, {"FORMA_AI_DEEPSEEK_API_KEY": "secret-key"}):
                response = supervisor.run(execute)
            self.assertEqual(response["payload"]["result"]["content"], "cloud result")
            self.assertEqual(adapter.execute.call_args.kwargs["api_key"], "secret-key")
            state = root / "state/cloud-proposals"
            self.assertEqual(list(state.glob(f"{preview['proposal_id']}.*")), [])

    def test_embedding_plan_failure_preserves_command_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "cache"
            cache.mkdir()
            catalog = root / "models.json"
            catalog.write_text('{"schema_version":1,"models":[]}', encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = supervisor.main([
                    "--request-id", "00000000-0000-0000-0000-000000000001",
                    "embedding-plan", "--root", str(root / "product"),
                    "--cache-root", str(cache), "--catalog", str(catalog),
                ])
            response = json.loads(output.getvalue())
            self.assertEqual(exit_code, 2)
            self.assertEqual(response["command"], "embedding-plan")
            self.assertEqual(response["status"], "error")

    def model(self):
        return ModelDefinition(
            id="fixture-model", repository="test/model", revision="a" * 40,
            license="Apache-2.0", license_url="https://example.test/license",
            model_type="fixture", architecture="Fixture", capabilities=("chat",), quantization_bits=4,
            embedding_dimension=None, query_prefix=None, document_prefix=None,
            files={"weights.bin": ModelFile(10, "b" * 64)},
        )

    def embedding_model(self):
        return ModelDefinition(
            id="fixture-embedding", repository="test/embedding", revision="c" * 40,
            license="MIT", license_url="https://example.test/license",
            model_type="bert", architecture="BertModel", capabilities=("embedding",),
            quantization_bits=None, embedding_dimension=384,
            query_prefix="query: ", document_prefix="passage: ",
            files={"weights.bin": ModelFile(10, "d" * 64)},
        )

    def test_embedding_download_requires_revision_and_delegates(self):
        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            cache = base / "cache"
            cache.mkdir()
            catalog = base / "models.json"
            catalog.write_text("{}", encoding="utf-8")
            args = supervisor.parser().parse_args([
                "--request-id", request_id, "download-embedding",
                "--root", str(base / "product"), "--cache-root", str(cache),
                "--catalog", str(catalog), "--approve-revision", "c" * 40,
            ])
            result = SimpleNamespace(to_dict=lambda: {
                "schema_version": 1, "model_id": "fixture-embedding",
                "revision": "c" * 40, "snapshot_path": str(cache / "snapshot"),
                "total_size_bytes": 10, "transferred_bytes": 10,
                "reused_files": 0, "downloaded_files": 1,
            })
            with patch.object(supervisor, "load_model", return_value=self.embedding_model()), \
                 patch.object(supervisor, "download_model_snapshot", return_value=result) as download:
                response = supervisor.run(args)
            self.assertEqual(response["command"], "download-embedding")
            self.assertEqual(response["payload"]["downloaded_files"], 1)
            download.assert_called_once_with(
                cache_root=cache, model=self.embedding_model(), approved_revision="c" * 40,
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

    def write_herdr_upstreams(self, directory: Path, payload: bytes) -> Path:
        manifest = directory / "upstreams.json"
        manifest.write_text(json.dumps({
            "components": [{
                "id": "herdr", "release": "v0.8.2", "artifacts": [{
                    "id": "macos-aarch64", "name": "herdr-macos-aarch64", "platform": "macos",
                    "architecture": "aarch64",
                    "minimum_macos_major": 11, "maximum_macos_major": 99,
                    "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                    "url": "https://github.com/herdrdev/herdr/releases/download/v0.8.2/herdr-macos-aarch64"
                }]
            }]
        }), encoding="utf-8")
        return manifest

    def test_installed_herdr_executable_resolves_verified_cached_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload = b"fixture-herdr-binary"
            upstreams = self.write_herdr_upstreams(base, payload)
            root = base / "Product"
            downloads = root / "cache" / "downloads"
            downloads.mkdir(parents=True)
            executable = downloads / "herdr-macos-aarch64"
            executable.write_bytes(payload)
            executable.chmod(0o755)
            resolved = supervisor._installed_herdr_executable(
                root, upstreams, os_major=15, architecture="aarch64",
            )
            self.assertEqual(resolved, executable)

    def test_installed_herdr_executable_rejects_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            payload = b"fixture-herdr-binary"
            upstreams = self.write_herdr_upstreams(base, payload)
            root = base / "Product"
            downloads = root / "cache" / "downloads"
            downloads.mkdir(parents=True)
            executable = downloads / "herdr-macos-aarch64"
            executable.write_bytes(b"tampered-binary-contents")
            executable.chmod(0o755)
            with self.assertRaisesRegex(ValueError, "digest verification"):
                supervisor._installed_herdr_executable(
                    root, upstreams, os_major=15, architecture="aarch64",
                )

    def test_installed_herdr_executable_rejects_missing_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            upstreams = self.write_herdr_upstreams(base, b"fixture-herdr-binary")
            root = base / "Product"
            with self.assertRaisesRegex(ValueError, "missing or unsafe"):
                supervisor._installed_herdr_executable(
                    root, upstreams, os_major=15, architecture="aarch64",
                )

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
                "--os-major", "15", "--architecture", "aarch64",
            ])
            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaisesRegex(ValueError, "runtime secrets"):
                    supervisor.run(args)
            duplicate = "same-secret-value-with-at-least-32-characters"
            with patch.dict("os.environ", {
                "OMLX_API_KEY": duplicate,
                "FORMA_AI_BROKER_TOKEN": duplicate,
                "FORMA_AI_MEMORY_TOKEN": "m" * 40,
            }, clear=True):
                with self.assertRaisesRegex(ValueError, "distinct"):
                    supervisor.run(args)
            with patch.dict("os.environ", {
                "OMLX_API_KEY": "o" * 40,
                "FORMA_AI_BROKER_TOKEN": duplicate,
                "FORMA_AI_MEMORY_TOKEN": duplicate,
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

    def test_approved_embedding_route_uses_managed_python_without_secret_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "start-runtime", "--root", str(root),
                "--os-major", "15", "--architecture", "aarch64",
            ])
            spec = SimpleNamespace(
                executable="/fixture/omlx", arguments=(),
                environment={"HOME": str(root / "state/homes/omlx"),
                             "TMPDIR": str(root / "state/runtime/omlx/tmp")},
                working_directory=str(root / "state/runtime/omlx"),
            )
            now = "2026-08-30T00:00:00+00:00"
            runtime = RuntimeRecord(1, "running", args.request_id, None, None, None, None, None, 1, now, now)
            environment = {
                "OMLX_API_KEY": "o" * 40,
                "FORMA_AI_BROKER_TOKEN": "b" * 40,
                "FORMA_AI_MEMORY_TOKEN": "m" * 40,
            }
            route = ApprovedEmbeddingRoute(
                "fixture-embedding", "fixture/embedding", "a" * 40, 384,
                "query: ", "passage: ",
            )
            with patch.dict("os.environ", environment, clear=True), \
                 patch.object(supervisor, "_installed_herdr_executable", return_value=Path("/fixture/herdr")), \
                 patch.object(supervisor, "_installed_omlx_executable", return_value=Path("/fixture/omlx")), \
                 patch.object(supervisor, "omlx_process_spec", return_value=spec), \
                 patch.object(supervisor, "load_approved_embedding_route", return_value=route), \
                 patch.object(SemanticaRuntimeInspector, "status", return_value={"installation": "verified"}), \
                 patch.object(supervisor.SemanticaLayout, "python", return_value=Path("/managed/python")), \
                 patch.object(supervisor, "_memory_runtime_entrypoint", return_value=Path("/bundle/runtime.py")), \
                 patch.object(supervisor.RuntimeManager, "start", return_value=runtime) as start:
                supervisor.run(args)
            memory = start.call_args.kwargs["memory"]
            self.assertEqual(memory["executable"], Path("/managed/python"))
            self.assertIn("fixture/embedding", memory["arguments"])
            self.assertIn("query: ", memory["arguments"])
            self.assertIn("passage: ", memory["arguments"])
            self.assertNotIn("o" * 40, memory["arguments"])
            self.assertNotIn("m" * 40, memory["arguments"])
            self.assertEqual(memory["environment"]["OMLX_API_KEY"], "o" * 40)
            self.assertEqual(memory["environment"]["FORMA_AI_MEMORY_TOKEN"], "m" * 40)
            herdr = start.call_args.kwargs["herdr"]
            self.assertEqual(herdr["executable"], Path("/fixture/herdr"))
            self.assertEqual(herdr["arguments"], ("--session", "forma-workbench", "server"))
            self.assertTrue(callable(start.call_args.kwargs["herdr_probe"]))

    def test_runtime_status_reports_herdr_alive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            args = supervisor.parser().parse_args([
                "--request-id", str(uuid.uuid4()), "runtime-status", "--root", str(root),
            ])
            with patch.object(supervisor.RuntimeManager, "status", return_value={
                "phase": "running", "record": None, "omlx_alive": True,
                "broker_alive": True, "memory_alive": True, "herdr_alive": True,
            }):
                response = supervisor.run(args)
            self.assertTrue(response["payload"]["herdr_alive"])

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
                "FORMA_AI_BROKER_TOKEN": "b" * 40,
                "FORMA_AI_MEMORY_TOKEN": "m" * 40,
            }, clear=True), patch.object(supervisor.RuntimeManager, "status", return_value={"phase": "stopped"}), \
                 patch.object(supervisor, "_sample_task") as sample:
                with self.assertRaisesRegex(ValueError, "not running"):
                    supervisor.run(args)
            sample.assert_not_called()

    def tool_route_common(self, root: Path, request_id: str, command: str) -> argparse.Namespace:
        return supervisor.parser().parse_args([
            "--request-id", request_id, command,
            "--root", str(root),
            "--catalog", str(ROOT / "config/tool-routing.json"),
            "--capability-id", "echo.transform",
            "--operation", "echo",
            "--arguments-json", '{"message":"hello"}',
            "--data-class", "tool_result",
        ])

    def test_tool_route_resolve_maps_installed_capability(self):
        from forma_ai.tool_registry import ToolRegistry

        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            ToolRegistry(
                root,
                catalog_path=ROOT / "config/tool-packages.json",
                repository_root=ROOT,
            ).install("fixture-echo-mcp")
            response = supervisor.run(self.tool_route_common(root, request_id, "tool-route-resolve"))
        self.assertEqual(response["command"], "tool-route-resolve")
        decision = response["payload"]["decision"]
        self.assertEqual(decision["route"], "ready")
        self.assertEqual(decision["tool_id"], "fixture-echo-mcp")
        self.assertEqual(decision["mcp_tool_name"], "echo")
        self.assertFalse(decision["approval_required"])

    def test_tool_route_resolve_reports_missing_tool(self):
        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            response = supervisor.run(self.tool_route_common(root, request_id, "tool-route-resolve"))
        self.assertEqual(response["payload"]["decision"]["route"], "tool_missing")

    def test_tool_call_propose_persists_proposal_without_exposing_arguments(self):
        from forma_ai.tool_registry import ToolRegistry

        request_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Product"
            ToolRegistry(
                root,
                catalog_path=ROOT / "config/tool-packages.json",
                repository_root=ROOT,
            ).install("fixture-echo-mcp")
            response = supervisor.run(self.tool_route_common(root, request_id, "tool-call-propose"))
            proposal = response["payload"]["proposal"]
            self.assertFalse(response["payload"]["approval_required"])
            self.assertTrue(proposal["proposal_id"])
            state = root / "state/tool-proposals"
            self.assertTrue((state / f"{proposal['proposal_id']}.json").is_file())
            self.assertTrue((state / f"{proposal['proposal_id']}.payload").is_file())
            self.assertNotIn("hello", json.dumps(response))
            audit = (root / "logs/audit/tools.jsonl").read_text(encoding="utf-8")
            self.assertIn('"event":"tool_route_proposed"', audit)
            self.assertNotIn("hello", audit)


class SupervisorHerdrFeatureTests(unittest.TestCase):
    def test_herdr_dispatch_fails_closed_when_feature_is_disabled(self):
        herdr = Mock()
        instance = Supervisor(features=SupervisorFeatures(), herdr=herdr)

        with self.assertRaisesRegex(
            SupervisorFeatureUnavailable, "HERDR_EXECUTION_DISABLED"
        ):
            instance.dispatch_agent_task(
                task_id="task-001",
                correlation_id="corr-001",
                agent_name="forma-task-001",
                agent_kind="codex",
                pane_id="pane-001",
            )

        herdr.spawn_task.assert_not_called()

    def test_enabled_herdr_dispatch_delegates_exactly_once(self):
        expected = object()
        herdr = Mock()
        herdr.spawn_task.return_value = expected
        instance = Supervisor(
            features=SupervisorFeatures(herdr_execution_enabled=True),
            herdr=herdr,
        )

        result = instance.dispatch_agent_task(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )

        self.assertIs(result, expected)
        herdr.spawn_task.assert_called_once_with(
            task_id="task-001",
            correlation_id="corr-001",
            agent_name="forma-task-001",
            agent_kind="codex",
            pane_id="pane-001",
        )


if __name__ == "__main__":
    unittest.main()
