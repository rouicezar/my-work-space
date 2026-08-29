import hashlib
import plistlib
import shutil
import tempfile
import unittest
from contextlib import AbstractContextManager
from pathlib import Path

from mac_ai_work_os.artifacts import ArtifactExpectation
from mac_ai_work_os.downloads import DownloadResult
from mac_ai_work_os.installer import INSTALL_STEPS, InstallError, OMLXInstallLayout, OMLXInstaller
from mac_ai_work_os.macos_bundle import AppInspection


PAYLOAD = b"fixture-dmg"


def expected():
    return ArtifactExpectation(
        component="omlx",
        release="v0.6.3",
        artifact_id="fixture",
        name="omlx.dmg",
        size_bytes=len(PAYLOAD),
        sha256=hashlib.sha256(PAYLOAD).hexdigest(),
        url="https://github.com/example/omlx.dmg",
    )


def make_app(path: Path):
    (path / "Contents/MacOS").mkdir(parents=True)
    (path / "Contents/MacOS/omlx").write_bytes(b"binary")
    with (path / "Contents/Info.plist").open("wb") as handle:
        plistlib.dump(
            {
                "CFBundleIdentifier": "app.omlx",
                "CFBundleShortVersionString": "0.6.3",
                "CFBundleVersion": "1",
                "CFBundleExecutable": "omlx",
            },
            handle,
        )


def inspection(path: Path, version: str, *, valid=True):
    return AppInspection(
        schema_version=1,
        path=str(path),
        bundle_identifier="app.omlx",
        short_version=version,
        build_version="1",
        minimum_macos="15.0",
        executable="omlx",
        architectures=["arm64"],
        codesign_valid=valid,
        gatekeeper_accepted=valid,
        expected_version=version,
        version_matches=valid,
        arm64_supported=valid,
        valid=valid,
        evidence={},
        errors=[] if valid else [{"code": "INVALID", "message": "fixture"}],
    )


class FakeDownloader:
    def __init__(self, payload=PAYLOAD):
        self.calls = 0
        self.payload = payload

    def fetch(self, artifact, directory, progress=None):
        self.calls += 1
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / artifact.name
        path.write_bytes(self.payload)
        return DownloadResult(path, len(self.payload), 0, False)


class FixtureMount(AbstractContextManager):
    def __init__(self, source_root: Path, calls: list[str]):
        self.source_root = source_root
        self.calls = calls

    def __enter__(self):
        self.calls.append("mount")
        return self.source_root

    def __exit__(self, *args):
        self.calls.append("detach")


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.layout = OMLXInstallLayout(self.root / "Product")
        self.source = self.root / "mounted"
        make_app(self.source / "oMLX.app")
        self.mount_calls = []
        self.downloader = FakeDownloader()

    def tearDown(self):
        self.temp.cleanup()

    def installer(self, *, copy=shutil.copytree, inspect=lambda path, version: inspection(path, version)):
        return OMLXInstaller(
            self.layout,
            expected(),
            downloader=self.downloader,
            mount=lambda image, mountpoint: FixtureMount(self.source, self.mount_calls),
            copy=copy,
            inspect=inspect,
        )

    def test_install_verifies_source_and_stage_then_atomically_activates(self):
        installer = self.installer()
        active = installer.run()
        self.assertEqual(active.release, "v0.6.3")
        self.assertEqual(active.bundle_identifier, "app.omlx")
        self.assertTrue(Path(active.app_path).is_dir())
        self.assertEqual(self.mount_calls, ["mount", "detach"])
        state = installer.journal.load()
        self.assertEqual(state.phase, "completed")
        self.assertEqual(state.completed_steps, INSTALL_STEPS)
        self.assertEqual(self.layout.active_record.stat().st_mode & 0o777, 0o600)

    def test_copy_failure_preserves_old_active_record_and_resumes_same_operation(self):
        self.layout.active_record.parent.mkdir(parents=True)
        self.layout.active_record.write_text(
            '{"schema_version":1,"component":"omlx","release":"old","artifact_sha256":"old",'
            '"app_path":"/old","bundle_identifier":"app.omlx","short_version":"old",'
            '"activated_at":"before"}\n'
        )
        calls = [0]

        def flaky_copy(source, destination):
            calls[0] += 1
            if calls[0] == 1:
                raise InstallError("COPY_FAILED", "interrupted")
            shutil.copytree(source, destination)

        installer = self.installer(copy=flaky_copy)
        with self.assertRaisesRegex(InstallError, "interrupted"):
            installer.run()
        failed = installer.journal.load()
        self.assertEqual(failed.phase, "failed")
        self.assertEqual(failed.active_step, "stage_bundle")
        self.assertEqual(installer.load_active().release, "old")

        active = installer.run()
        self.assertEqual(active.release, "v0.6.3")
        self.assertEqual(installer.journal.load().operation_id, failed.operation_id)

    def test_resume_replaces_only_incomplete_staging_for_same_operation(self):
        calls = [0]

        def interrupted_copy(source, destination):
            calls[0] += 1
            if calls[0] == 1:
                (destination / "Contents").mkdir(parents=True)
                (destination / "Contents/partial").write_text("interrupted", encoding="utf-8")
                raise InstallError("COPY_FAILED", "interrupted after partial copy")
            shutil.copytree(source, destination)

        installer = self.installer(
            copy=interrupted_copy,
            inspect=lambda path, version: inspection(
                path, version, valid=(path / "Contents/Info.plist").is_file()
            ),
        )
        with self.assertRaisesRegex(InstallError, "interrupted after partial copy"):
            installer.run()
        failed = installer.journal.load()
        staging_root = self.layout.version_root("v0.6.3") / f".staging-{failed.operation_id}"
        self.assertTrue((staging_root / "oMLX.app/Contents/partial").is_file())

        active = installer.run()

        self.assertEqual(active.release, "v0.6.3")
        self.assertEqual(calls[0], 2)
        self.assertFalse(staging_root.exists())
        self.assertEqual(installer.journal.load().operation_id, failed.operation_id)

    def test_invalid_source_never_copies_or_activates(self):
        copied = []
        installer = self.installer(
            copy=lambda source, destination: copied.append((source, destination)),
            inspect=lambda path, version: inspection(path, version, valid=False),
        )
        with self.assertRaises(InstallError) as failed:
            installer.run()
        self.assertEqual(failed.exception.code, "SOURCE_BUNDLE_INVALID")
        self.assertEqual(copied, [])
        self.assertFalse(self.layout.active_record.exists())

    def test_artifact_is_reverified_immediately_before_mount(self):
        self.downloader = FakeDownloader(payload=b"tampered!!")
        installer = self.installer()
        with self.assertRaises(InstallError) as failed:
            installer.run()
        self.assertEqual(failed.exception.code, "ARTIFACT_INTEGRITY_FAILED")
        self.assertEqual(self.mount_calls, [])
        self.assertFalse(self.layout.active_record.exists())


if __name__ == "__main__":
    unittest.main()
