"""Unit tests for the managed Semantica installer."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess

from forma_ai.semantica_installer import (
    SemanticaInstallError,
    SemanticaInstaller,
    SemanticaInstallLayout,
)
from forma_ai.semantica_runtime import (
    EXPECTED_COMMIT,
    EXPECTED_RELEASE,
    EXPECTED_VERSION,
)


class SemanticaInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Product"
        self.layout = SemanticaInstallLayout(self.root)
        self.created_venv = False
        self.installed = False
        self.pip_calls: list[list[str]] = []

    def tearDown(self) -> None:
        self.temp.cleanup()

    def venv_creator(self, version_root: Path) -> None:
        self.created_venv = True
        python = version_root / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text("fixture-python", encoding="utf-8")
        python.chmod(0o700)

    def pip_installer(self, python: Path) -> None:
        self.installed = True
        self.assertEqual(python, self.layout.python())
        self.pip_calls.append(["managed-install"])

    def runner(self, command, **kwargs):
        module = self.layout.version_root() / "lib/python3.12/site-packages/semantica/__init__.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("fixture", encoding="utf-8")
        return CompletedProcess(
            command,
            0,
            json.dumps({"version": EXPECTED_VERSION, "module_path": str(module)}),
            "",
        )

    def test_install_creates_venv_pip_active_record_and_verifies(self) -> None:
        installer = SemanticaInstaller(
            self.layout,
            venv_creator=self.venv_creator,
            pip_installer=self.pip_installer,
            runner=self.runner,
        )
        active = installer.install()
        self.assertTrue(self.created_venv)
        self.assertTrue(self.installed)
        self.assertEqual(self.pip_calls, [["managed-install"]])
        self.assertEqual(active["schema_version"], 1)
        self.assertEqual(active["component"], "semantica")
        self.assertEqual(active["release"], EXPECTED_RELEASE)
        self.assertEqual(active["package_version"], EXPECTED_VERSION)
        self.assertEqual(active["source_commit"], EXPECTED_COMMIT)
        self.assertEqual(active["python_path"], str(self.layout.python()))
        record = json.loads(self.layout.active_record.read_text(encoding="utf-8"))
        self.assertEqual(record["python_path"], str(self.layout.python()))
        self.assertIn("activated_at", record)

    def test_install_fails_when_verification_does_not_pass(self) -> None:
        def failing_runner(command, **kwargs):
            return CompletedProcess(command, 1, "", "import failed")

        installer = SemanticaInstaller(
            self.layout,
            venv_creator=self.venv_creator,
            pip_installer=self.pip_installer,
            runner=failing_runner,
        )
        with self.assertRaises(SemanticaInstallError) as raised:
            installer.install()
        self.assertEqual(raised.exception.code, "SEMANTICA_IMPORT_FAILED")
        self.assertTrue(self.layout.active_record.is_file())

    def test_existing_incomplete_venv_path_fails_closed(self) -> None:
        version_root = self.layout.version_root()
        version_root.mkdir(parents=True)
        (version_root / "bin").mkdir()

        installer = SemanticaInstaller(
            self.layout,
            venv_creator=self.venv_creator,
            pip_installer=self.pip_installer,
            runner=self.runner,
        )
        with self.assertRaises(SemanticaInstallError) as raised:
            installer.install()
        self.assertEqual(raised.exception.code, "SEMANTICA_VENV_EXISTS")


if __name__ == "__main__":
    unittest.main()
