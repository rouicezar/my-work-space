"""Unit tests for managed Semantica runtime proof logic."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from forma_ai.semantica_runtime_proof import (
    evaluate_worker_payload,
    probe_omlx_embedding_route,
    redact_proof_evidence,
    run_semantica_runtime_proof,
)


class EvaluateWorkerPayloadTests(unittest.TestCase):
    def test_complete_payload_passes(self) -> None:
        evidence = evaluate_worker_payload(
            {
                "store_id": "mem-1",
                "retrieved": True,
                "reloaded": True,
                "forgotten": True,
                "embedding_mode": "fixture",
            }
        )
        self.assertEqual(evidence["status"], "proof_passed")
        self.assertEqual(evidence["embedding_mode"], "fixture")

    def test_missing_store_id_fails(self) -> None:
        evidence = evaluate_worker_payload(
            {
                "store_id": "",
                "retrieved": True,
                "reloaded": True,
                "forgotten": True,
            }
        )
        self.assertEqual(evidence["status"], "proof_failed")
        self.assertEqual(evidence["reason"], "store_failed")

    def test_missing_fields_fails(self) -> None:
        evidence = evaluate_worker_payload({"store_id": "mem-1"})
        self.assertEqual(evidence["status"], "proof_failed")
        self.assertEqual(evidence["reason"], "worker_payload_incomplete")


class ProbeOmlxEmbeddingRouteTests(unittest.TestCase):
    @patch("forma_ai.semantica_runtime_proof.OMLXEmbeddingClient")
    def test_probe_success(self, client_cls) -> None:
        client_cls.return_value.probe.return_value = {
            "status": "healthy",
            "model": "fixture-model",
            "dimension": 8,
        }
        result = probe_omlx_embedding_route(
            port=8000,
            api_key="x" * 32,
            embedding_model="fixture-model",
            expected_dimension=8,
        )
        self.assertEqual(result["status"], "healthy")

    @patch("forma_ai.semantica_runtime_proof.OMLXEmbeddingClient")
    def test_probe_failure_is_unavailable(self, client_cls) -> None:
        from forma_ai.omlx_embeddings import EmbeddingError

        client_cls.return_value.probe.side_effect = EmbeddingError("EMBEDDING_TIMEOUT", "timed out")
        result = probe_omlx_embedding_route(
            port=8000,
            api_key="x" * 32,
            embedding_model="fixture-model",
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["code"], "EMBEDDING_TIMEOUT")


class RunSemanticaRuntimeProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Product"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def activate(self) -> None:
        layout_python = self.root / "runtimes/semantica/v0.6.7/bin/python"
        layout_python.parent.mkdir(parents=True)
        layout_python.write_text("fixture", encoding="utf-8")
        layout_python.chmod(0o700)
        active_record = self.root / "state/components/semantica-active.json"
        active_record.parent.mkdir(parents=True)
        active_record.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "component": "semantica",
                    "release": "v0.6.7",
                    "package_version": "0.6.7",
                    "source_commit": "ecb33a5b7d1c232da77527da89d861e2b10e9c42",
                    "python_path": str(layout_python),
                    "activated_at": "2026-08-30T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )

    def inspector_runner(self, command, **kwargs):
        module = self.root / "runtimes/semantica/v0.6.7/lib/python3.12/site-packages/semantica/__init__.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("fixture", encoding="utf-8")
        return CompletedProcess(
            command,
            0,
            json.dumps({"version": "0.6.7", "module_path": str(module)}),
            "",
        )

    def worker_runner(self, command, **kwargs):
        if "-I" in command and str(command[-1]).endswith("semantica_proof_worker.py"):
            return CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "store_id": "mem-proof-1",
                        "retrieved": True,
                        "reloaded": True,
                        "forgotten": True,
                        "embedding_mode": "fixture",
                    }
                ),
                "",
            )
        return self.inspector_runner(command, **kwargs)

    def test_uninstalled_environment_fails_honestly(self) -> None:
        evidence = run_semantica_runtime_proof(self.root)
        self.assertEqual(evidence["status"], "proof_failed")
        self.assertEqual(evidence["reason"], "installation_not_verified")

    def test_verified_installation_runs_fixture_worker(self) -> None:
        self.activate()
        evidence = run_semantica_runtime_proof(self.root, runner=self.worker_runner)
        self.assertEqual(evidence["status"], "proof_passed")
        self.assertEqual(evidence["embedding_mode"], "fixture")
        self.assertEqual(evidence["installation"], "verified")

    @patch("forma_ai.semantica_runtime_proof.probe_omlx_embedding_route")
    def test_omlx_probe_failure_falls_back_to_fixture(self, probe) -> None:
        probe.return_value = {"status": "unavailable", "code": "EMBEDDING_TIMEOUT"}
        self.activate()
        evidence = run_semantica_runtime_proof(
            self.root,
            omlx_port=8000,
            omlx_api_key="x" * 32,
            embedding_model="fixture-model",
            runner=self.worker_runner,
        )
        self.assertEqual(evidence["status"], "proof_passed")
        self.assertEqual(evidence["embedding_mode"], "fixture")
        self.assertEqual(evidence["embedding_probe"]["code"], "EMBEDDING_TIMEOUT")

    @patch("forma_ai.semantica_runtime_proof.probe_omlx_embedding_route")
    def test_omlx_probe_success_records_probe_metadata(self, probe) -> None:
        probe.return_value = {"status": "healthy", "model": "fixture-model", "dimension": 8}

        def omlx_worker_runner(command, **kwargs):
            if "-I" in command and str(command[-1]).endswith("semantica_proof_worker.py"):
                return CompletedProcess(
                    command,
                    0,
                    json.dumps(
                        {
                            "store_id": "mem-proof-1",
                            "retrieved": True,
                            "reloaded": True,
                            "forgotten": True,
                            "embedding_mode": "omlx",
                        }
                    ),
                    "",
                )
            return self.inspector_runner(command, **kwargs)

        self.activate()
        evidence = run_semantica_runtime_proof(
            self.root,
            omlx_port=8000,
            omlx_api_key="x" * 32,
            embedding_model="fixture-model",
            expected_dimension=8,
            runner=omlx_worker_runner,
        )
        self.assertEqual(evidence["status"], "proof_passed")
        self.assertEqual(evidence["embedding_mode"], "omlx")
        self.assertEqual(evidence["embedding_probe"]["status"], "healthy")


class RedactProofEvidenceTests(unittest.TestCase):
    def test_redacts_secret_like_keys(self) -> None:
        sanitized = redact_proof_evidence(
            {
                "status": "proof_passed",
                "OMLX_API_KEY": "super-secret-key-value",
                "embedding_probe": {"status": "healthy"},
            }
        )
        self.assertEqual(sanitized["OMLX_API_KEY"], "[redacted]")


if __name__ == "__main__":
    unittest.main()
