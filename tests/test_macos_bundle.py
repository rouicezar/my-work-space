import plistlib
import tempfile
import unittest
from pathlib import Path

from mac_ai_work_os.macos_bundle import CommandEvidence, inspect_app


def fake_runner(results):
    def run(args):
        command = tuple(args[:2])
        return results.get(command, CommandEvidence(list(args), 0, "", ""))

    return run


class MacOSBundleInspectionTests(unittest.TestCase):
    def create_app(self, root: Path, version="0.6.3") -> Path:
        app = root / "oMLX.app"
        macos = app / "Contents/MacOS"
        macos.mkdir(parents=True)
        (macos / "oMLX").write_bytes(b"fixture")
        info = {
            "CFBundleIdentifier": "ai.jundot.oMLX",
            "CFBundleShortVersionString": version,
            "CFBundleVersion": "1",
            "CFBundleExecutable": "oMLX",
            "LSMinimumSystemVersion": "15.0",
        }
        with (app / "Contents/Info.plist").open("wb") as handle:
            plistlib.dump(info, handle)
        return app

    def test_valid_bundle_requires_version_arch_signature_and_gatekeeper(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.create_app(Path(directory))
            runner = fake_runner(
                {
                    ("/usr/bin/lipo", "-archs"): CommandEvidence([], 0, "arm64 x86_64", ""),
                    ("/usr/bin/codesign", "--verify"): CommandEvidence([], 0, "", "valid"),
                    ("/usr/sbin/spctl", "-a"): CommandEvidence([], 0, "", "accepted"),
                }
            )
            report = inspect_app(app, "0.6.3", runner)
        self.assertTrue(report.valid)
        self.assertEqual(report.architectures, ["arm64", "x86_64"])
        self.assertTrue(report.codesign_valid)
        self.assertTrue(report.gatekeeper_accepted)

    def test_gatekeeper_rejection_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.create_app(Path(directory))
            runner = fake_runner(
                {
                    ("/usr/bin/lipo", "-archs"): CommandEvidence([], 0, "arm64", ""),
                    ("/usr/bin/codesign", "--verify"): CommandEvidence([], 0, "", ""),
                    ("/usr/sbin/spctl", "-a"): CommandEvidence([], 1, "", "rejected"),
                }
            )
            report = inspect_app(app, "0.6.3", runner)
        self.assertFalse(report.valid)
        self.assertFalse(report.gatekeeper_accepted)
        self.assertIn("GATEKEEPER_REJECTED", {error["code"] for error in report.errors})

    def test_version_mismatch_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.create_app(Path(directory), version="0.6.2")
            runner = fake_runner(
                {
                    ("/usr/bin/lipo", "-archs"): CommandEvidence([], 0, "arm64", ""),
                    ("/usr/bin/codesign", "--verify"): CommandEvidence([], 0, "", ""),
                    ("/usr/sbin/spctl", "-a"): CommandEvidence([], 0, "", "accepted"),
                }
            )
            report = inspect_app(app, "0.6.3", runner)
        self.assertFalse(report.valid)
        self.assertIn("VERSION_MISMATCH", {error["code"] for error in report.errors})


if __name__ == "__main__":
    unittest.main()
