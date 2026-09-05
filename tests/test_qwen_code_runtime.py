import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from forma_ai.artifacts import ArtifactExpectation
from forma_ai.qwen_code_runtime import (
    QwenCodeInstallError,
    QwenCodeInstallLayout,
    QwenCodeInstaller,
    prepare_qwen_agent_environment,
)


class QwenCodeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = Path(self.tempdir.name)
        self.root = self.base / "Product"
        self.root.mkdir()

    def tearDown(self):
        self.tempdir.cleanup()

    def archive(self, *, traversal=False):
        path = self.base / "qwen-code-darwin-arm64.tar.gz"
        with tarfile.open(path, "w:gz") as bundle:
            files = {
                "qwen-code/manifest.json": b'{"version":"0.23.0"}\n',
                "qwen-code/LICENSE": b"Apache License 2.0\n",
                "qwen-code/bin/qwen": b"#!/bin/sh\necho 0.23.0\n",
            }
            if traversal:
                files["../escape"] = b"unsafe"
            for name, body in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(body)
                info.mode = 0o755 if name.endswith("/qwen") else 0o644
                bundle.addfile(info, io.BytesIO(body))
        return path

    def expected(self, archive):
        import hashlib

        payload = archive.read_bytes()
        return ArtifactExpectation(
            component="qwen-code",
            release="v0.23.0",
            artifact_id="macos-aarch64",
            name=archive.name,
            size_bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            url="https://github.com/QwenLM/qwen-code/releases/download/v0.23.0/qwen-code-darwin-arm64.tar.gz",
        )

    def test_installs_verified_archive_and_writes_private_active_record(self):
        archive = self.archive()
        layout = QwenCodeInstallLayout(self.root)
        active = QwenCodeInstaller(layout, self.expected(archive)).install_archive(archive)

        self.assertEqual(active.release, "v0.23.0")
        self.assertEqual(active.version, "0.23.0")
        self.assertEqual(Path(active.executable_path), layout.executable("v0.23.0"))
        self.assertTrue(os.access(active.executable_path, os.X_OK))
        self.assertEqual(layout.active_record.stat().st_mode & 0o777, 0o600)
        self.assertEqual(layout.cached_archive.stat().st_mode & 0o777, 0o600)
        self.assertEqual(QwenCodeInstaller(layout, self.expected(archive)).load_active(), active)

    def test_rejects_archive_path_escape(self):
        archive = self.archive(traversal=True)
        with self.assertRaisesRegex(QwenCodeInstallError, "QWEN_ARCHIVE_UNSAFE"):
            QwenCodeInstaller(
                QwenCodeInstallLayout(self.root), self.expected(archive)
            ).install_archive(archive)
        self.assertFalse((self.base / "escape").exists())

    def test_private_agent_environment_is_loopback_and_denies_builtin_actions(self):
        archive = self.archive()
        layout = QwenCodeInstallLayout(self.root)
        QwenCodeInstaller(layout, self.expected(archive)).install_archive(archive)
        environment = prepare_qwen_agent_environment(
            layout,
            expected=self.expected(archive),
            broker_token="broker-token",
            broker_port=43110,
            model_id="Qwen3-0.6B-4bit",
        )

        self.assertEqual(environment["HOME"], str(layout.agent_home))
        self.assertEqual(environment["OPENAI_BASE_URL"], "http://127.0.0.1:43110/v1")
        self.assertEqual(environment["OPENAI_MODEL"], "Qwen3-0.6B-4bit")
        self.assertEqual(environment["QWEN_TELEMETRY_ENABLED"], "false")
        self.assertEqual(environment["PATH"].split(":", 1)[0], str(layout.herdr_launcher.parent))
        self.assertEqual(
            environment["FORMA_QWEN_REAL_EXECUTABLE"],
            str(layout.executable("v0.23.0")),
        )
        self.assertTrue(os.access(layout.herdr_launcher, os.X_OK))
        self.assertNotIn(" exec ", layout.herdr_launcher.read_text(encoding="utf-8"))
        self.assertIn("< /dev/tty &", layout.herdr_launcher.read_text(encoding="utf-8"))
        self.assertNotIn("HTTPS_PROXY", environment)
        settings = json.loads(layout.settings.read_text(encoding="utf-8"))
        self.assertTrue(settings["ui"]["showStatusInTitle"])
        self.assertEqual(settings["tools"]["approvalMode"], "plan")
        self.assertFalse(settings["telemetry"]["enabled"])
        self.assertFalse(settings["general"]["chatRecording"])
        self.assertEqual(settings['context']['fileName'], ['.forma-context.md'])
        self.assertFalse(settings["memory"]["enableManagedAutoMemory"])
        denied = set(settings["permissions"]["deny"])
        self.assertTrue({"Bash", "Read", "Edit", "WebFetch", "task", "skill"} <= denied)
        self.assertEqual(settings["mcpServers"], {})
        self.assertEqual(layout.settings.stat().st_mode & 0o777, 0o600)

    def test_only_product_governed_mcp_server_is_exposed(self):
        archive = self.archive()
        layout = QwenCodeInstallLayout(self.root)
        QwenCodeInstaller(layout, self.expected(archive)).install_archive(archive)
        server = self.base / "governed.py"
        server.write_text("# fixture\n", encoding="utf-8")
        prepare_qwen_agent_environment(
            layout, expected=self.expected(archive), broker_token="broker-token",
            broker_port=43110, model_id="Qwen3-4B-4bit",
            mcp_server_path=server, repository_root=self.base,
        )
        settings = json.loads(layout.settings.read_text(encoding="utf-8"))
        self.assertEqual(set(settings["mcpServers"]), {"forma-governed-tools"})
        configured = settings["mcpServers"]["forma-governed-tools"]
        self.assertEqual(configured["includeTools"], ["forma_governed_tool"])
        self.assertIs(configured["trust"], True)
        self.assertIn(str(server), configured["args"])

    def test_non_loopback_or_invalid_broker_port_fails_closed(self):
        archive = self.archive()
        layout = QwenCodeInstallLayout(self.root)
        QwenCodeInstaller(layout, self.expected(archive)).install_archive(archive)
        with self.assertRaisesRegex(QwenCodeInstallError, "QWEN_PROVIDER_NOT_LOCAL"):
            prepare_qwen_agent_environment(
                layout,
                expected=self.expected(archive),
                broker_token="token",
                broker_port=80,
                model_id="Qwen3-0.6B-4bit",
            )


if __name__ == "__main__":
    unittest.main()
