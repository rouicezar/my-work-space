"""Verified, product-owned Qwen Code runtime installation and isolation."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from forma_ai.artifacts import ArtifactExpectation, verify_file
from forma_ai.models import _atomic_json


class QwenCodeInstallError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class QwenCodeInstallLayout:
    root: Path

    @property
    def downloads(self) -> Path:
        return self.root / "cache" / "downloads"

    @property
    def cached_archive(self) -> Path:
        return self.downloads / "qwen-code-darwin-arm64.tar.gz"

    @property
    def component_root(self) -> Path:
        return self.root / "runtimes" / "qwen-code"

    @property
    def active_record(self) -> Path:
        return self.root / "state" / "components" / "qwen-code-active.json"

    @property
    def agent_home(self) -> Path:
        return self.root / "state" / "homes" / "qwen-agent"

    @property
    def settings(self) -> Path:
        return self.agent_home / ".qwen" / "settings.json"

    @property
    def herdr_launcher(self) -> Path:
        return self.agent_home / "bin" / "qwen"

    def version_root(self, release: str) -> Path:
        return self.component_root / release

    def installation(self, release: str) -> Path:
        return self.version_root(release) / "qwen-code"

    def executable(self, release: str) -> Path:
        return self.installation(release) / "bin" / "qwen"


@dataclass(frozen=True)
class ActiveQwenCodeRuntime:
    schema_version: int
    component: str
    release: str
    version: str
    artifact_sha256: str
    archive_path: str
    executable_path: str
    activated_at: str


class QwenCodeInstaller:
    def __init__(self, layout: QwenCodeInstallLayout, expected: ArtifactExpectation) -> None:
        self.layout = layout
        self.expected = expected
        if expected.component != "qwen-code":
            raise QwenCodeInstallError("QWEN_ARTIFACT_INVALID", expected.component)

    def install_archive(self, archive: Path) -> ActiveQwenCodeRuntime:
        if not archive.is_file() or archive.is_symlink():
            raise QwenCodeInstallError("QWEN_ARTIFACT_MISSING", str(archive))
        if not verify_file(archive, self.expected).valid:
            raise QwenCodeInstallError("QWEN_ARTIFACT_INTEGRITY_FAILED", str(archive))
        self.layout.downloads.mkdir(parents=True, exist_ok=True)
        if archive.resolve() != self.layout.cached_archive.resolve(strict=False):
            temporary = self.layout.downloads / f".{self.layout.cached_archive.name}.tmp"
            shutil.copyfile(archive, temporary)
            os.chmod(temporary, 0o600)
            if not verify_file(temporary, self.expected).valid:
                temporary.unlink(missing_ok=True)
                raise QwenCodeInstallError("QWEN_ARTIFACT_INTEGRITY_FAILED", str(temporary))
            os.replace(temporary, self.layout.cached_archive)
        else:
            os.chmod(self.layout.cached_archive, 0o600)
        self._stage()
        return self._activate()

    def load_active(self) -> ActiveQwenCodeRuntime:
        try:
            record = ActiveQwenCodeRuntime(
                **json.loads(self.layout.active_record.read_text(encoding="utf-8"))
            )
        except (OSError, TypeError, json.JSONDecodeError) as exc:
            raise QwenCodeInstallError("QWEN_ACTIVE_RECORD_INVALID", str(exc)) from exc
        expected_executable = self.layout.executable(self.expected.release)
        if (
            record.schema_version != 1
            or record.component != "qwen-code"
            or record.release != self.expected.release
            or record.artifact_sha256 != self.expected.sha256
            or Path(record.archive_path) != self.layout.cached_archive
            or Path(record.executable_path) != expected_executable
            or not verify_file(self.layout.cached_archive, self.expected).valid
        ):
            raise QwenCodeInstallError("QWEN_ACTIVE_RECORD_INVALID", "binding mismatch")
        self._validate_installation()
        return record

    def _stage(self) -> None:
        destination = self.layout.installation(self.expected.release)
        if destination.exists():
            self._validate_installation()
            return
        version_root = self.layout.version_root(self.expected.release)
        version_root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".qwen-stage-", dir=version_root))
        try:
            with tarfile.open(self.layout.cached_archive, "r:gz") as bundle:
                members = bundle.getmembers()
                for member in members:
                    relative = PurePosixPath(member.name)
                    if (
                        relative.is_absolute()
                        or ".." in relative.parts
                        or not relative.parts
                        or relative.parts[0] != "qwen-code"
                        or not (member.isfile() or member.isdir())
                    ):
                        raise QwenCodeInstallError("QWEN_ARCHIVE_UNSAFE", member.name)
                for member in members:
                    target = staging.joinpath(*PurePosixPath(member.name).parts)
                    if member.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = bundle.extractfile(member)
                    if source is None:
                        raise QwenCodeInstallError("QWEN_ARCHIVE_UNSAFE", member.name)
                    with source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    os.chmod(target, member.mode & 0o755)
            staged = staging / "qwen-code"
            self._validate_tree(staged)
            os.replace(staged, destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def _activate(self) -> ActiveQwenCodeRuntime:
        version = self._validate_installation()
        record = ActiveQwenCodeRuntime(
            schema_version=1,
            component="qwen-code",
            release=self.expected.release,
            version=version,
            artifact_sha256=self.expected.sha256,
            archive_path=str(self.layout.cached_archive),
            executable_path=str(self.layout.executable(self.expected.release)),
            activated_at=datetime.now(timezone.utc).isoformat(),
        )
        _atomic_json(self.layout.active_record, asdict(record))
        return record

    def _validate_installation(self) -> str:
        return self._validate_tree(self.layout.installation(self.expected.release))

    def _validate_tree(self, installation: Path) -> str:
        executable = installation / "bin" / "qwen"
        manifest = installation / "manifest.json"
        license_file = installation / "LICENSE"
        if installation.is_symlink() or any(
            not path.is_file() or path.is_symlink()
            for path in (executable, manifest, license_file)
        ):
            raise QwenCodeInstallError("QWEN_INSTALLATION_INVALID", str(installation))
        try:
            version = str(json.loads(manifest.read_text(encoding="utf-8"))["version"])
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise QwenCodeInstallError("QWEN_INSTALLATION_INVALID", str(exc)) from exc
        if version != self.expected.release.removeprefix("v"):
            raise QwenCodeInstallError("QWEN_VERSION_MISMATCH", version)
        if not os.access(executable, os.X_OK):
            raise QwenCodeInstallError("QWEN_EXECUTABLE_INVALID", str(executable))
        return version


_DENIED_QWEN_TOOLS = (
    "Bash",
    "Read",
    "Edit",
    "WebFetch",
    "web_search",
    "task",
    "agent",
    "list_agents",
    "send_message",
    "skill",
    "tool_search",
    "computer_use",
    "image_gen",
    "task_stop",
    "monitor",
)


_HERDR_QWEN_LAUNCHER = b'''#!/bin/sh
set -eu
: "${FORMA_QWEN_REAL_EXECUTABLE:?missing verified Qwen executable}"
"$FORMA_QWEN_REAL_EXECUTABLE" "$@" < /dev/tty &
child=$!
trap 'kill -TERM "$child" 2>/dev/null || true' HUP INT TERM
wait "$child"
'''


def _prepare_herdr_launcher(layout: QwenCodeInstallLayout, executable: Path) -> Path:
    launcher = layout.herdr_launcher
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if launcher.is_symlink() or (launcher.exists() and not launcher.is_file()):
        raise QwenCodeInstallError("QWEN_LAUNCHER_UNSAFE", str(launcher))
    descriptor, name = tempfile.mkstemp(prefix=".qwen-launcher-", dir=launcher.parent)
    temporary = Path(name)
    os.fchmod(descriptor, 0o700)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_HERDR_QWEN_LAUNCHER)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, launcher)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    if executable.is_symlink() or not executable.is_file() or not os.access(executable, os.X_OK):
        raise QwenCodeInstallError("QWEN_EXECUTABLE_INVALID", str(executable))
    return launcher


def prepare_qwen_agent_environment(
    layout: QwenCodeInstallLayout,
    *,
    expected: ArtifactExpectation,
    broker_token: str,
    broker_port: int,
    model_id: str,
    mcp_server_path: Path | None = None,
    repository_root: Path | None = None,
) -> dict[str, str]:
    if not 1024 <= broker_port <= 65535:
        raise QwenCodeInstallError("QWEN_PROVIDER_NOT_LOCAL", str(broker_port))
    if not broker_token or not model_id:
        raise QwenCodeInstallError("QWEN_CONFIGURATION_INVALID", "missing token or model")
    active = QwenCodeInstaller(layout, expected).load_active()
    layout.settings.parent.mkdir(parents=True, exist_ok=True)
    if mcp_server_path is None:
        mcp_servers = {}
    else:
        if (
            not mcp_server_path.is_absolute() or not mcp_server_path.is_file()
            or mcp_server_path.is_symlink() or repository_root is None
            or not repository_root.is_absolute()
        ):
            raise QwenCodeInstallError("QWEN_MCP_SERVER_INVALID", str(mcp_server_path))
        mcp_servers = {
            "forma-governed-tools": {
                "command": sys.executable,
                "args": [
                    *(["internal-qwen-mcp"] if getattr(sys, "frozen", False) else [str(mcp_server_path)]),
                    "--root", str(layout.root),
                    "--repository-root", str(repository_root),
                    "--catalog", str(repository_root / "config/tool-routing.json"),
                ],
                "includeTools": ["forma_governed_tool"],
                "trust": True,
            }
        }
    settings = {
        "$version": 4,
        "general": {"chatRecording": False},
        "context": {"fileName": [".forma-context.md"], "includeDirectories": [],
                    "loadFromIncludeDirectories": False,
                    "fileFiltering": {"enableRecursiveFileSearch": False}},
        "ui": {"showStatusInTitle": True},
        "telemetry": {"enabled": False, "logPrompts": False},
        "memory": {
            "enableManagedAutoMemory": False,
            "enableManagedAutoDream": False,
            "enableAutoSkill": False,
            "enableTeamMemory": False,
            "enableTeamMemorySync": False,
        },
        "tools": {"approvalMode": "plan"},
        "permissions": {"allow": [], "ask": [], "deny": list(_DENIED_QWEN_TOOLS)},
        "mcpServers": mcp_servers,
        "disableAllHooks": True,
    }
    _atomic_json(layout.settings, settings)
    executable = Path(active.executable_path)
    launcher = _prepare_herdr_launcher(layout, executable)
    return {
        "HOME": str(layout.agent_home),
        "PATH": f"{launcher.parent}:/usr/bin:/bin:/usr/sbin:/sbin",
        "FORMA_QWEN_REAL_EXECUTABLE": str(executable),
        "NO_PROXY": "127.0.0.1,localhost,::1",
        "OPENAI_API_KEY": broker_token,
        "OPENAI_BASE_URL": f"http://127.0.0.1:{broker_port}/v1",
        "OPENAI_MODEL": model_id,
        "QWEN_MODEL": model_id,
        "QWEN_TELEMETRY_ENABLED": "false",
        "QWEN_DISABLED_SLASH_COMMANDS": "update,extensions,channel,hooks,mcp,skills,agents",
    }
