import subprocess
import tempfile
import unittest
import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingScriptTests(unittest.TestCase):
    def test_app_bundle_declares_native_application_principal_class(self):
        with (ROOT / "prototypes/packaging/App-Info.plist").open("rb") as handle:
            info = plistlib.load(handle)
        self.assertEqual(info["CFBundlePackageType"], "APPL")
        self.assertEqual(info["NSPrincipalClass"], "NSApplication")
        self.assertEqual(info["CFBundleName"], "Forma AI")
        self.assertEqual(info["CFBundleIconFile"], "FormaAI")

    def test_app_bundle_includes_forma_ai_icon(self):
        icon = ROOT / "prototypes/packaging/Resources/FormaAI.icns"
        self.assertTrue(icon.is_file())
        self.assertGreater(icon.stat().st_size, 100_000)
        script = (ROOT / "prototypes/packaging/build-app.sh").read_text(encoding="utf-8")
        self.assertIn('Resources/FormaAI.icns" "$APP/Contents/Resources/FormaAI.icns', script)

    def test_app_bundle_includes_pinned_upstream_manifest(self):
        script = (ROOT / "prototypes/packaging/build-app.sh").read_text(encoding="utf-8")
        self.assertIn('config/upstreams.json" "$APP/Contents/Resources/upstreams.json', script)
        self.assertIn('config/models.json" "$APP/Contents/Resources/models.json', script)
        self.assertIn(
            'config/cloud-providers.json" "$APP/Contents/Resources/cloud-providers.json',
            script,
        )
        self.assertIn(
            'config/local-model-profiles.json" "$APP/Contents/Resources/local-model-profiles.json',
            script,
        )
        self.assertIn('evidence/runtime/private-local-task-2026-08-30.md', script)
        self.assertIn('Contents/Helpers/MemoryRuntime', script)
        self.assertIn('semantica_memory_runtime.py', script)
        self.assertIn('semantica_backend.py', script)

    def test_supervisor_build_rejects_relative_output_before_tool_download(self):
        result = subprocess.run(
            ["./prototypes/packaging/build-supervisor.sh", "relative-output"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be absolute", result.stderr)

    def test_supervisor_build_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["./prototypes/packaging/build-supervisor.sh", directory],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)

    def test_app_build_refuses_existing_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "Forma AI.app"
            app.mkdir()
            result = subprocess.run(
                ["./prototypes/packaging/build-app.sh", directory],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)


if __name__ == "__main__":
    unittest.main()
