import subprocess
import tempfile
import unittest
import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingScriptTests(unittest.TestCase):
    def test_build_places_supervisor_at_product_paths_location(self) -> None:
        source = (ROOT / "prototypes/packaging/Sources/FormaAIApp/ProductPaths.swift").read_text()
        build = (ROOT / "prototypes/packaging/build-app.sh").read_text()
        self.assertIn('Contents/Helpers/Supervisor', source)
        self.assertIn('$APP/Contents/Helpers/Supervisor', build)

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

    def test_app_build_rejects_legacy_manifest_overview_shell(self):
        script = (ROOT / "prototypes/packaging/build-app.sh").read_text(encoding="utf-8")
        self.assertIn("ManifestOverview", script)
        self.assertIn("DailyWorkbenchShell(presentation: .production)", script)
        self.assertIn("NavigationSplitView", script)
        self.assertIn("WorkspaceSection", script)

    def test_release_entry_uses_product_root_or_daily_workbench_shell(self):
        source = (ROOT / "prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift").read_text(
            encoding="utf-8"
        )
        app_dir = ROOT / "prototypes/packaging/Sources/FormaAIApp"
        self.assertNotIn("ManifestOverview", source)
        self.assertNotIn("struct DailyWorkbench: View", source)
        self.assertIn("#else", source)
        release_block = source.split("#else", 1)[1].split("#endif", 1)[0]
        self.assertTrue(
            "ProductRootView()" in release_block
            or "DailyWorkbenchShell(presentation: .production)" in release_block
        )
        for path in app_dir.glob("*.swift"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("NavigationSplitView", text, msg=str(path))
            self.assertNotIn("dailyNavRow", text, msg=str(path))
            self.assertNotIn("What would you like to work on?", text, msg=str(path))


    def test_production_settings_use_control_panels(self):
        shell = (ROOT / "prototypes/packaging/Sources/FormaAIApp/DailyWorkbenchShell.swift").read_text(encoding="utf-8")
        self.assertIn("LocalRuntimeControlPanel", shell)
        self.assertIn("ModelsProvidersControlPanel", shell)
        self.assertIn("DiagnosticsRecoveryControlPanel", shell)
        build = (ROOT / "prototypes/packaging/build-app.sh").read_text(encoding="utf-8")
        self.assertIn("download-model", (ROOT / "scripts/supervisor.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
