"""Recoverable installation for the pinned Semantica managed Python runtime."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from forma_ai.models import _atomic_json
from forma_ai.semantica_runtime import (
    EXPECTED_COMMIT,
    EXPECTED_RELEASE,
    EXPECTED_VERSION,
    SemanticaLayout,
    SemanticaRuntimeInspector,
    Runner,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANAGED_REQUIREMENTS = REPOSITORY_ROOT / "config" / "semantica-managed-requirements.txt"


class SemanticaInstallError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SemanticaInstallLayout(SemanticaLayout):
    """Install-time layout; reuses the read-only Semantica path contract."""


VenvCreator = Callable[[Path], None]
PipInstaller = Callable[[Path], None]


def _default_venv_creator(version_root: Path) -> None:
    version_root.parent.mkdir(parents=True, exist_ok=True)
    python = version_root / "bin" / "python"
    if python.exists():
        return
    if version_root.exists():
        raise SemanticaInstallError("SEMANTICA_VENV_EXISTS", str(version_root))
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(version_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "venv creation failed"
        raise SemanticaInstallError("SEMANTICA_VENV_FAILED", message)


def _pip_run(python: Path, *args: str) -> None:
    resolved = python.resolve(strict=False)
    if not resolved.is_file() or not resolved.stat().st_mode & 0o111:
        raise SemanticaInstallError("SEMANTICA_PYTHON_MISSING", str(python))
    result = subprocess.run(
        [str(python), "-m", "pip", "install", "--default-timeout", "300", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "pip install failed"
        raise SemanticaInstallError("SEMANTICA_PIP_FAILED", message)


def _default_pip_installer(python: Path) -> None:
    if not MANAGED_REQUIREMENTS.is_file():
        raise SemanticaInstallError(
            "SEMANTICA_REQUIREMENTS_MISSING",
            str(MANAGED_REQUIREMENTS),
        )
    _pip_run(python, "--no-deps", f"semantica=={EXPECTED_VERSION}")
    _pip_run(python, "-r", str(MANAGED_REQUIREMENTS))


class SemanticaInstaller:
    def __init__(
        self,
        layout: SemanticaInstallLayout,
        *,
        venv_creator: VenvCreator = _default_venv_creator,
        pip_installer: PipInstaller = _default_pip_installer,
        runner: Runner = subprocess.run,
    ):
        self.layout = layout
        self.venv_creator = venv_creator
        self.pip_installer = pip_installer
        self.runner = runner

    def install(self) -> dict[str, object]:
        version_root = self.layout.version_root()
        python = self.layout.python()
        self._ensure_safe_version_root(version_root)
        self.venv_creator(version_root)
        self.pip_installer(python)
        record = {
            "schema_version": 1,
            "component": "semantica",
            "release": EXPECTED_RELEASE,
            "package_version": EXPECTED_VERSION,
            "source_commit": EXPECTED_COMMIT,
            "python_path": str(python),
            "activated_at": datetime.now(timezone.utc).isoformat(),
        }
        _atomic_json(self.layout.active_record, record)
        status = SemanticaRuntimeInspector(self.layout, runner=self.runner).status()
        if status.get("installation") != "verified":
            code = str(status.get("code", "SEMANTICA_VERIFY_FAILED"))
            raise SemanticaInstallError(code, "managed Semantica installation did not verify")
        return record

    @staticmethod
    def _ensure_safe_version_root(version_root: Path) -> None:
        if not version_root.exists():
            return
        python = version_root / "bin" / "python"
        if not python.exists():
            raise SemanticaInstallError("SEMANTICA_VENV_EXISTS", str(version_root))
