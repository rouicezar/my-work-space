import json
import os
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess

from mac_ai_work_os.semantica_runtime import (
    EXPECTED_COMMIT,
    EXPECTED_RELEASE,
    EXPECTED_VERSION,
    SemanticaLayout,
    SemanticaRuntimeInspector,
)


class SemanticaRuntimeInspectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Product"
        self.layout = SemanticaLayout(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def activate(self):
        python = self.layout.python()
        python.parent.mkdir(parents=True)
        python.write_text("fixture", encoding="utf-8")
        python.chmod(0o700)
        self.layout.active_record.parent.mkdir(parents=True)
        self.layout.active_record.write_text(json.dumps({
            "schema_version": 1,
            "component": "semantica",
            "release": EXPECTED_RELEASE,
            "package_version": EXPECTED_VERSION,
            "source_commit": EXPECTED_COMMIT,
            "python_path": str(python),
            "activated_at": "2026-08-30T00:00:00+00:00",
        }), encoding="utf-8")

    def runner(self, command, **kwargs):
        module = self.layout.version_root() / "lib/python3.12/site-packages/semantica/__init__.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("fixture", encoding="utf-8")
        return CompletedProcess(command, 0, json.dumps({
            "version": EXPECTED_VERSION,
            "module_path": str(module),
        }), "")

    def test_absent_environment_is_honestly_unavailable_without_creating_state(self):
        status = SemanticaRuntimeInspector(self.layout).status()
        self.assertEqual(status["installation"], "not_installed")
        self.assertEqual(status["code"], "SEMANTICA_NOT_INSTALLED")
        self.assertFalse(self.root.exists())

    def test_verified_library_still_fails_closed_without_embedding_route(self):
        self.activate()
        status = SemanticaRuntimeInspector(self.layout, runner=self.runner).status()
        self.assertEqual(status["installation"], "verified")
        self.assertEqual(status["library"], "verified")
        self.assertEqual(status["agent_context"], "importable")
        self.assertEqual(status["status"], "unavailable")
        self.assertEqual(status["embedding"]["code"], "EMBEDDING_ROUTE_UNVERIFIED")

    def test_configured_route_is_not_claimed_healthy_without_real_probe(self):
        self.activate()
        status = SemanticaRuntimeInspector(self.layout, runner=self.runner).status(
            embedding_route="omlx://embedding-model"
        )
        self.assertEqual(status["embedding"]["status"], "configured_unverified")
        self.assertEqual(status["code"], "EMBEDDING_ROUTE_PROBE_REQUIRED")
        self.assertEqual(status["status"], "unavailable")

    def test_active_record_must_bind_exact_managed_runtime(self):
        self.activate()
        record = json.loads(self.layout.active_record.read_text())
        record["python_path"] = "/tmp/developer-environment/bin/python"
        self.layout.active_record.write_text(json.dumps(record), encoding="utf-8")
        status = SemanticaRuntimeInspector(self.layout, runner=self.runner).status()
        self.assertEqual(status["installation"], "invalid")
        self.assertEqual(status["code"], "SEMANTICA_ACTIVE_RECORD_MISMATCH")

    def test_module_import_must_resolve_inside_managed_runtime(self):
        self.activate()

        def outside(command, **kwargs):
            return CompletedProcess(command, 0, json.dumps({
                "version": EXPECTED_VERSION,
                "module_path": "/tmp/semantica/__init__.py",
            }), "")

        status = SemanticaRuntimeInspector(self.layout, runner=outside).status()
        self.assertEqual(status["code"], "SEMANTICA_MODULE_ESCAPES_RUNTIME")

    def test_probe_uses_isolated_offline_environment(self):
        self.activate()
        observed = {}

        def capture(command, **kwargs):
            observed["command"] = command
            observed.update(kwargs)
            return self.runner(command, **kwargs)

        SemanticaRuntimeInspector(self.layout, runner=capture).status()
        self.assertIn("-I", observed["command"])
        self.assertEqual(observed["env"]["HF_HUB_OFFLINE"], "1")
        self.assertEqual(observed["env"]["TRANSFORMERS_OFFLINE"], "1")
        self.assertNotIn("PYTHONPATH", observed["env"])


if __name__ == "__main__":
    unittest.main()
