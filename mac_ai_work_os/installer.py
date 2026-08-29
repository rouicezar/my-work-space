"""Recoverable, versioned oMLX installation transaction."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from mac_ai_work_os.artifacts import ArtifactExpectation, verify_file
from mac_ai_work_os.downloads import DownloadResult, ResumableDownloader
from mac_ai_work_os.lifecycle import LifecycleJournal, OperationState
from mac_ai_work_os.macos_bundle import AppInspection, inspect_app


INSTALL_STEPS = ["acquire_artifact", "stage_bundle", "activate_bundle"]


class InstallError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OMLXInstallLayout:
    root: Path

    @property
    def downloads(self) -> Path:
        return self.root / "cache" / "downloads"

    @property
    def operations(self) -> Path:
        return self.root / "state" / "operations" / "omlx-install"

    @property
    def component_root(self) -> Path:
        return self.root / "runtimes" / "omlx"

    @property
    def active_record(self) -> Path:
        return self.root / "state" / "components" / "omlx-active.json"

    def version_root(self, release: str) -> Path:
        return self.component_root / release

    def app(self, release: str) -> Path:
        return self.version_root(release) / "oMLX.app"


@dataclass(frozen=True)
class ActiveBundle:
    schema_version: int
    component: str
    release: str
    artifact_sha256: str
    app_path: str
    bundle_identifier: str
    short_version: str
    activated_at: str


class MountedImage(Protocol):
    def __enter__(self) -> Path: ...
    def __exit__(self, *args: object) -> None: ...


MountImage = Callable[[Path, Path], MountedImage]
CopyBundle = Callable[[Path, Path], None]
InspectBundle = Callable[[Path, str], AppInspection]


class MacOSDiskImage(AbstractContextManager[Path]):
    def __init__(self, image: Path, mountpoint: Path):
        self.image = image
        self.mountpoint = mountpoint
        self.attached = False

    def __enter__(self) -> Path:
        self.mountpoint.mkdir(parents=True, exist_ok=False)
        result = subprocess.run(
            [
                "/usr/bin/hdiutil",
                "attach",
                "-readonly",
                "-nobrowse",
                "-mountpoint",
                str(self.mountpoint),
                str(self.image),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            self.mountpoint.rmdir()
            raise InstallError("MOUNT_FAILED", result.stderr.strip() or result.stdout.strip())
        self.attached = True
        return self.mountpoint

    def __exit__(self, *args: object) -> None:
        if self.attached:
            result = subprocess.run(
                ["/usr/bin/hdiutil", "detach", str(self.mountpoint)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise InstallError("DETACH_FAILED", result.stderr.strip() or result.stdout.strip())
        self.mountpoint.rmdir()


def mount_image(image: Path, mountpoint: Path) -> MacOSDiskImage:
    return MacOSDiskImage(image, mountpoint)


def copy_bundle(source: Path, destination: Path) -> None:
    result = subprocess.run(
        ["/usr/bin/ditto", str(source), str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise InstallError("COPY_FAILED", result.stderr.strip() or result.stdout.strip())


class OMLXInstaller:
    def __init__(
        self,
        layout: OMLXInstallLayout,
        expected: ArtifactExpectation,
        *,
        downloader: ResumableDownloader,
        mount: MountImage = mount_image,
        copy: CopyBundle = copy_bundle,
        inspect: InspectBundle = inspect_app,
    ):
        self.layout = layout
        self.expected = expected
        self.downloader = downloader
        self.mount = mount
        self.copy = copy
        self.inspect = inspect
        self.journal = LifecycleJournal(layout.operations)

    def run(self) -> ActiveBundle:
        state = self._begin_or_resume()
        while state.phase != "completed":
            state = self.journal.start_next()
            if state.phase == "completed":
                break
            try:
                self._execute(state)
            except Exception as exc:
                code = exc.code if isinstance(exc, InstallError) else "INSTALL_STEP_FAILED"
                self.journal.fail_active(code, str(exc))
                raise
            state = self.journal.complete_active()
        return self.load_active()

    def load_active(self) -> ActiveBundle:
        try:
            return ActiveBundle(**json.loads(self.layout.active_record.read_text(encoding="utf-8")))
        except (OSError, TypeError, json.JSONDecodeError) as exc:
            raise InstallError("ACTIVE_RECORD_INVALID", str(exc)) from exc

    def _begin_or_resume(self) -> OperationState:
        current = self.journal.load_optional()
        if current and current.phase == "failed" and current.kind == "install" and current.steps == INSTALL_STEPS:
            return self.journal.resume_failed()
        return self.journal.begin("install", INSTALL_STEPS)

    def _execute(self, state: OperationState) -> None:
        if state.active_step == "acquire_artifact":
            self.downloader.fetch(self.expected, self.layout.downloads)
        elif state.active_step == "stage_bundle":
            self._stage(state.operation_id)
        elif state.active_step == "activate_bundle":
            self._activate()
        else:
            raise InstallError("UNKNOWN_INSTALL_STEP", str(state.active_step))

    def _stage(self, operation_id: str) -> None:
        artifact = self.layout.downloads / self.expected.name
        if not artifact.is_file():
            raise InstallError("ARTIFACT_MISSING", str(artifact))
        if not verify_file(artifact, self.expected).valid:
            raise InstallError("ARTIFACT_INTEGRITY_FAILED", str(artifact))
        destination = self.layout.app(self.expected.release)
        expected_version = self.expected.release.removeprefix("v")
        if destination.exists():
            if destination.is_symlink():
                raise InstallError("UNSAFE_BUNDLE_PATH", str(destination))
            self._require_valid(destination, expected_version, "INSTALLED_BUNDLE_INVALID")
            return

        version_root = self.layout.version_root(self.expected.release)
        version_root.mkdir(parents=True, exist_ok=True)
        staging_root = version_root / f".staging-{operation_id}"
        staging_app = staging_root / "oMLX.app"
        mountpoint = version_root / f".mount-{operation_id}"

        if staging_app.exists():
            if staging_app.is_symlink():
                raise InstallError("UNSAFE_BUNDLE_PATH", str(staging_app))
            try:
                self._require_valid(staging_app, expected_version, "STAGED_BUNDLE_INVALID")
            except InstallError as exc:
                if exc.code != "STAGED_BUNDLE_INVALID":
                    raise
                shutil.rmtree(staging_root)
        if not staging_app.exists():
            staging_root.mkdir(parents=True, exist_ok=True)
            with self.mount(artifact, mountpoint) as mounted:
                source = mounted / "oMLX.app"
                if source.is_symlink():
                    raise InstallError("UNSAFE_BUNDLE_PATH", str(source))
                self._require_valid(source, expected_version, "SOURCE_BUNDLE_INVALID")
                self.copy(source, staging_app)
            self._require_valid(staging_app, expected_version, "STAGED_BUNDLE_INVALID")

        os.replace(staging_app, destination)
        staging_root.rmdir()

    def _activate(self) -> None:
        app = self.layout.app(self.expected.release)
        inspection = self._require_valid(
            app, self.expected.release.removeprefix("v"), "INSTALLED_BUNDLE_INVALID"
        )
        record = ActiveBundle(
            schema_version=1,
            component="omlx",
            release=self.expected.release,
            artifact_sha256=self.expected.sha256,
            app_path=str(app),
            bundle_identifier=inspection.bundle_identifier or "",
            short_version=inspection.short_version or "",
            activated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._atomic_json(self.layout.active_record, asdict(record))

    def _require_valid(self, app: Path, expected_version: str, code: str) -> AppInspection:
        inspection = self.inspect(app, expected_version)
        if not inspection.valid:
            raise InstallError(code, json.dumps(inspection.errors, ensure_ascii=False))
        if inspection.bundle_identifier != "app.omlx":
            raise InstallError("BUNDLE_ID_MISMATCH", str(inspection.bundle_identifier))
        return inspection

    @staticmethod
    def _atomic_json(path: Path, data: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
        temporary = Path(temporary_name)
        os.fchmod(descriptor, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except Exception:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise
