"""Read-only verification for the product-managed Semantica environment."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


EXPECTED_RELEASE = "v0.6.7"
EXPECTED_VERSION = "0.6.7"
EXPECTED_COMMIT = "ecb33a5b7d1c232da77527da89d861e2b10e9c42"
class SemanticaRuntimeError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SemanticaLayout:
    root: Path

    @property
    def component_root(self) -> Path:
        return self.root / "runtimes" / "semantica"

    @property
    def active_record(self) -> Path:
        return self.root / "state" / "components" / "semantica-active.json"

    def version_root(self, release: str = EXPECTED_RELEASE) -> Path:
        return self.component_root / release

    def python(self, release: str = EXPECTED_RELEASE) -> Path:
        return self.version_root(release) / "bin" / "python"


Runner = Callable[..., subprocess.CompletedProcess[str]]


class SemanticaRuntimeInspector:
    def __init__(self, layout: SemanticaLayout, *, runner: Runner = subprocess.run):
        self.layout = layout
        self.runner = runner

    def status(self, *, embedding_route: str | None = None) -> dict[str, object]:
        base: dict[str, object] = {
            "schema_version": 1,
            "component": "semantica",
            "expected_release": EXPECTED_RELEASE,
            "expected_version": EXPECTED_VERSION,
            "expected_commit": EXPECTED_COMMIT,
            "managed_root": str(self.layout.version_root()),
            "installation": "not_installed",
            "library": "unavailable",
            "agent_context": "unavailable",
            "embedding": {
                "status": "unavailable",
                "code": "EMBEDDING_ROUTE_UNVERIFIED",
                "route": None,
            },
            "status": "unavailable",
            "code": "SEMANTICA_NOT_INSTALLED",
        }
        if not self.layout.active_record.exists() and not self.layout.active_record.is_symlink():
            return base
        try:
            record = self._load_record()
            probe = self._probe(Path(record["python_path"]))
        except SemanticaRuntimeError as exc:
            base["installation"] = "invalid"
            base["code"] = exc.code
            return base
        base.update(
            {
                "installation": "verified",
                "library": "verified",
                "agent_context": "importable",
                "package_version": probe["version"],
                "module_path": probe["module_path"],
                "code": "EMBEDDING_ROUTE_UNVERIFIED",
            }
        )
        if embedding_route:
            base["embedding"] = {
                "status": "configured_unverified",
                "code": "EMBEDDING_ROUTE_PROBE_REQUIRED",
                "route": embedding_route,
            }
            base["code"] = "EMBEDDING_ROUTE_PROBE_REQUIRED"
        return base

    def _load_record(self) -> dict[str, object]:
        path = self.layout.active_record
        if not path.is_file() or path.is_symlink():
            raise SemanticaRuntimeError("SEMANTICA_ACTIVE_RECORD_UNSAFE", str(path))
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SemanticaRuntimeError("SEMANTICA_ACTIVE_RECORD_INVALID", str(path)) from exc
        expected_python = self.layout.python()
        if (
            record.get("schema_version") != 1
            or record.get("component") != "semantica"
            or record.get("release") != EXPECTED_RELEASE
            or record.get("package_version") != EXPECTED_VERSION
            or record.get("source_commit") != EXPECTED_COMMIT
            or record.get("python_path") != str(expected_python)
        ):
            raise SemanticaRuntimeError("SEMANTICA_ACTIVE_RECORD_MISMATCH", str(path))
        return record

    def _probe(self, python: Path) -> dict[str, str]:
        if not python.is_file() or not os.access(python, os.X_OK):
            raise SemanticaRuntimeError("SEMANTICA_PYTHON_MISSING", str(python))
        script = (
            "import json,pathlib,semantica;"
            "from semantica.context import AgentContext;"
            "print(json.dumps({'version':semantica.__version__,"
            "'module_path':str(pathlib.Path(semantica.__file__).resolve())}))"
        )
        environment = {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(self.layout.root / "state" / "homes" / "semantica-probe"),
            "TMPDIR": str(self.layout.root / "state" / "runtime" / "semantica" / "tmp"),
            "NO_PROXY": "127.0.0.1,localhost,::1",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        }
        try:
            result = self.runner(
                [str(python), "-I", "-c", script],
                capture_output=True,
                text=True,
                check=False,
                timeout=15.0,
                env=environment,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SemanticaRuntimeError("SEMANTICA_PROBE_FAILED", type(exc).__name__) from exc
        if result.returncode != 0:
            raise SemanticaRuntimeError("SEMANTICA_IMPORT_FAILED", "managed import failed")
        try:
            payload = json.loads(result.stdout)
            version = payload["version"]
            module_path = Path(payload["module_path"]).resolve(strict=False)
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise SemanticaRuntimeError("SEMANTICA_PROBE_INVALID", "invalid probe response") from exc
        if version != EXPECTED_VERSION:
            raise SemanticaRuntimeError("SEMANTICA_VERSION_MISMATCH", str(version))
        try:
            module_path.relative_to(self.layout.version_root().resolve(strict=False))
        except ValueError as exc:
            raise SemanticaRuntimeError("SEMANTICA_MODULE_ESCAPES_RUNTIME", str(module_path)) from exc
        if not module_path.is_file():
            raise SemanticaRuntimeError("SEMANTICA_MODULE_MISSING", str(module_path))
        return {"version": version, "module_path": str(module_path)}
