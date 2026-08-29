import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingScriptTests(unittest.TestCase):
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
            app = Path(directory) / "Mac AI Work OS.app"
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
