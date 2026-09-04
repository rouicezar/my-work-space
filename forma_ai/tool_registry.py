"""Local-first MCP tool discovery, versioned install, and start/stop lifecycle."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol

from forma_ai.mcp_client import MCPServerSpec
from forma_ai.models import _atomic_json


LOCAL_MANIFEST = "mcp-tool.json"
PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-+][A-Za-z0-9._-]+)?$")


class ToolRegistryError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ToolArtifact:
    name: str
    source: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ToolPackageDefinition:
    package_id: str
    version: str
    description: str
    command: str
    args: tuple[str, ...]
    artifact: ToolArtifact


@dataclass(frozen=True)
class ToolInstallation:
    tool_id: str
    version: str
    source: str
    command: str
    args: tuple[str, ...]
    install_dir: Path | None
    manifest_path: Path | None

    def server_spec(self) -> MCPServerSpec:
        install_dir = "" if self.install_dir is None else str(self.install_dir)
        rendered = tuple(
            part.replace("{install_dir}", install_dir)
            for part in self.args
        )
        return MCPServerSpec(command=self.command, args=rendered)


@dataclass(frozen=True)
class ToolProcessState:
    tool_id: str
    pid: int
    command: str
    args: tuple[str, ...]
    started_at: str


class ArtifactSource(Protocol):
    def copy(self, *, source: Path, destination: Path) -> None: ...


class LocalArtifactSource:
    def __init__(self, repository_root: Path) -> None:
        if not repository_root.is_absolute():
            raise ToolRegistryError("REPOSITORY_ROOT_INVALID", str(repository_root))
        self.repository_root = repository_root

    def copy(self, *, source: Path, destination: Path) -> None:
        origin = source if source.is_absolute() else self.repository_root / source
        if not origin.is_file() or origin.is_symlink():
            raise ToolRegistryError("TOOL_ARTIFACT_MISSING", str(origin))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, destination)


class ToolRegistry:
    """Discover local tools first, install pinned packages, and manage MCP processes."""

    def __init__(
        self,
        product_root: Path,
        *,
        catalog_path: Path,
        repository_root: Path,
        local_paths: Iterable[Path] = (),
        artifact_source: ArtifactSource | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not product_root.is_absolute():
            raise ToolRegistryError("PRODUCT_ROOT_INVALID", str(product_root))
        self.product_root = product_root
        self.catalog_path = catalog_path
        self.repository_root = repository_root
        self.local_paths = tuple(_normalize_local_paths(local_paths))
        self.artifact_source = artifact_source or LocalArtifactSource(repository_root)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.state_root = product_root / "state/tools"
        self.index_path = self.state_root / "installed.json"
        self.running_root = self.state_root / "running"
        self._processes_by_tool_id: dict[str, subprocess.Popen[bytes]] = {}

    def discover(self) -> tuple[ToolInstallation, ...]:
        discovered: dict[str, ToolInstallation] = {}
        for installation in self._discover_installed():
            discovered[installation.tool_id] = installation
        for installation in self._discover_local():
            discovered[installation.tool_id] = installation
        return tuple(sorted(discovered.values(), key=lambda item: item.tool_id))

    def install(self, package_id: str) -> ToolInstallation:
        package = load_tool_package(self.catalog_path, package_id)
        install_dir = self.state_root / "packages" / package.package_id / package.version
        self.state_root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".tool-staging-", dir=self.state_root))
        try:
            destination = staging / package.artifact.name
            self.artifact_source.copy(source=Path(package.artifact.source), destination=destination)
            verification = _verify_artifact(destination, package.artifact)
            if not verification.valid:
                raise ToolRegistryError("TOOL_ARTIFACT_VERIFY_FAILED", package.package_id)
            install_dir.parent.mkdir(parents=True, exist_ok=True)
            if install_dir.exists():
                shutil.rmtree(install_dir)
            os.replace(staging, install_dir)
            staging = None
        finally:
            if staging is not None:
                shutil.rmtree(staging, ignore_errors=True)
        record = {
            "schema_version": 1,
            "tool_id": package.package_id,
            "version": package.version,
            "source": "registry",
            "command": package.command,
            "args": list(package.args),
            "install_dir": str(install_dir),
            "artifact_sha256": package.artifact.sha256,
            "installed_at": self._now().isoformat(),
        }
        index = self._load_index()
        index[package.package_id] = record
        _atomic_json(self.index_path, {"schema_version": 1, "tools": index})
        return ToolInstallation(
            tool_id=package.package_id,
            version=package.version,
            source="registry",
            command=package.command,
            args=package.args,
            install_dir=install_dir,
            manifest_path=None,
        )

    def start(self, tool_id: str) -> ToolProcessState:
        installation = self.get(tool_id)
        if self.is_running(tool_id):
            raise ToolRegistryError("TOOL_ALREADY_RUNNING", tool_id)
        spec = installation.server_spec()
        log_path = self.state_root / "logs" / f"{tool_id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(log_path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        try:
            process = subprocess.Popen(
                spec.argv(),
                cwd=installation.install_dir or self.product_root,
                stdin=subprocess.PIPE,
                stdout=descriptor,
                stderr=subprocess.STDOUT,
                close_fds=True,
            )
        finally:
            os.close(descriptor)
        self._processes_by_tool_id[tool_id] = process
        state = ToolProcessState(
            tool_id=tool_id,
            pid=process.pid,
            command=spec.command,
            args=spec.args,
            started_at=self._now().isoformat(),
        )
        self.running_root.mkdir(parents=True, exist_ok=True)
        _atomic_json(self.running_root / f"{tool_id}.json", asdict(state))
        return state

    def stop(self, tool_id: str) -> None:
        path = self.running_root / f"{tool_id}.json"
        if not path.is_file():
            raise ToolRegistryError("TOOL_NOT_RUNNING", tool_id)
        state = ToolProcessState(**json.loads(path.read_text(encoding="utf-8")))
        process = self._processes_by_tool_id.pop(tool_id, None)
        if process is not None:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
            path.unlink(missing_ok=True)
            return
        try:
            os.kill(state.pid, signal.SIGTERM)
        except ProcessLookupError as exc:
            raise ToolRegistryError("TOOL_PROCESS_MISSING", tool_id) from exc
        for _ in range(20):
            try:
                os.kill(state.pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            os.kill(state.pid, signal.SIGKILL)
        path.unlink(missing_ok=True)

    def is_running(self, tool_id: str) -> bool:
        path = self.running_root / f"{tool_id}.json"
        if not path.is_file():
            return False
        state = ToolProcessState(**json.loads(path.read_text(encoding="utf-8")))
        process = self._processes_by_tool_id.get(tool_id)
        if process is not None:
            if process.poll() is None:
                return True
            self._processes_by_tool_id.pop(tool_id, None)
            path.unlink(missing_ok=True)
            return False
        try:
            os.kill(state.pid, 0)
        except ProcessLookupError:
            path.unlink(missing_ok=True)
            return False
        return True

    def get(self, tool_id: str) -> ToolInstallation:
        for installation in self.discover():
            if installation.tool_id == tool_id:
                return installation
        raise ToolRegistryError("TOOL_NOT_FOUND", tool_id)

    def _discover_local(self) -> tuple[ToolInstallation, ...]:
        installations: list[ToolInstallation] = []
        for root in self.local_paths:
            for path in sorted(root.rglob(LOCAL_MANIFEST)):
                if path.is_symlink():
                    continue
                installations.append(_installation_from_local_manifest(path))
        return tuple(installations)

    def _discover_installed(self) -> tuple[ToolInstallation, ...]:
        index = self._load_index()
        installations: list[ToolInstallation] = []
        for record in index.values():
            install_dir = Path(record["install_dir"])
            if not install_dir.is_dir():
                continue
            installations.append(
                ToolInstallation(
                    tool_id=record["tool_id"],
                    version=record["version"],
                    source=record["source"],
                    command=record["command"],
                    args=tuple(record["args"]),
                    install_dir=install_dir,
                    manifest_path=None,
                )
            )
        return tuple(installations)

    def _load_index(self) -> dict[str, dict[str, Any]]:
        if not self.index_path.is_file():
            return {}
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        tools = data.get("tools")
        if not isinstance(tools, dict):
            raise ToolRegistryError("TOOL_INDEX_INVALID", str(self.index_path))
        return tools


def load_tool_package(catalog_path: Path, package_id: str) -> ToolPackageDefinition:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ToolRegistryError("TOOL_CATALOG_INVALID", "unsupported schema")
    matches = [item for item in data.get("packages", []) if item.get("id") == package_id]
    if len(matches) != 1:
        raise ToolRegistryError("TOOL_PACKAGE_NOT_FOUND", package_id)
    item = matches[0]
    package = str(item.get("id", ""))
    version = str(item.get("version", ""))
    if not PACKAGE_ID.fullmatch(package) or not VERSION.fullmatch(version):
        raise ToolRegistryError("TOOL_PACKAGE_INVALID", package_id)
    command = str(item.get("command", ""))
    if not command:
        raise ToolRegistryError("TOOL_PACKAGE_INVALID", package_id)
    args = item.get("args", [])
    if not isinstance(args, list) or not all(isinstance(value, str) for value in args):
        raise ToolRegistryError("TOOL_PACKAGE_INVALID", package_id)
    artifact_raw = item.get("artifact")
    if not isinstance(artifact_raw, dict):
        raise ToolRegistryError("TOOL_PACKAGE_INVALID", package_id)
    digest = str(artifact_raw.get("sha256", ""))
    if len(digest) != 64:
        raise ToolRegistryError("TOOL_PACKAGE_INVALID", package_id)
    size = artifact_raw.get("size_bytes")
    if not isinstance(size, int) or size <= 0:
        raise ToolRegistryError("TOOL_PACKAGE_INVALID", package_id)
    name = str(artifact_raw.get("name", ""))
    source = str(artifact_raw.get("source", ""))
    if not name or not source:
        raise ToolRegistryError("TOOL_PACKAGE_INVALID", package_id)
    return ToolPackageDefinition(
        package_id=package,
        version=version,
        description=str(item.get("description", "")),
        command=command,
        args=tuple(args),
        artifact=ToolArtifact(name=name, source=source, size_bytes=size, sha256=digest),
    )


def _installation_from_local_manifest(path: Path) -> ToolInstallation:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ToolRegistryError("TOOL_MANIFEST_INVALID", str(path))
    tool_id = str(data.get("id", ""))
    version = str(data.get("version", ""))
    command = str(data.get("command", ""))
    args = data.get("args", [])
    if (
        not PACKAGE_ID.fullmatch(tool_id)
        or not VERSION.fullmatch(version)
        or not command
        or not isinstance(args, list)
        or not all(isinstance(value, str) for value in args)
    ):
        raise ToolRegistryError("TOOL_MANIFEST_INVALID", str(path))
    working_directory = data.get("working_directory")
    base = path.parent if working_directory in (None, ".", "") else (path.parent / working_directory).resolve()
    rendered_args = tuple(str(base / arg) if not Path(arg).is_absolute() else arg for arg in args)
    return ToolInstallation(
        tool_id=tool_id,
        version=version,
        source="local",
        command=command,
        args=rendered_args,
        install_dir=base,
        manifest_path=path,
    )


@dataclass(frozen=True)
class ArtifactVerification:
    expected_size_bytes: int
    actual_size_bytes: int
    expected_sha256: str
    actual_sha256: str
    valid: bool


def _verify_artifact(path: Path, artifact: ToolArtifact) -> ArtifactVerification:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    actual = digest.hexdigest()
    return ArtifactVerification(
        expected_size_bytes=artifact.size_bytes,
        actual_size_bytes=size,
        expected_sha256=artifact.sha256,
        actual_sha256=actual,
        valid=size == artifact.size_bytes and actual == artifact.sha256,
    )


def _normalize_local_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    normalized: list[Path] = []
    for path in paths:
        if not path.is_absolute():
            raise ToolRegistryError("TOOL_LOCAL_PATH_INVALID", str(path))
        resolved = path.resolve()
        if not resolved.is_dir() or resolved.is_symlink():
            raise ToolRegistryError("TOOL_LOCAL_PATH_INVALID", str(path))
        normalized.append(resolved)
    return tuple(normalized)
