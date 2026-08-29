import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallCLITests(unittest.TestCase):
    def test_help_runs_from_repository_root(self):
        result = subprocess.run(
            [sys.executable, "scripts/install_omlx.py", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--root", result.stdout)

    def test_relative_root_fails_before_network_or_install(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/install_omlx.py",
                "--root",
                "relative",
                "--os-major",
                "26",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("ROOT_NOT_ABSOLUTE", result.stdout)

    def test_invalid_upstream_manifest_is_reported_as_structured_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "upstreams.json"
            invalid.write_text("not json", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/install_omlx.py",
                    "--root",
                    str(Path(directory) / "Product"),
                    "--os-major",
                    "26",
                    "--upstreams",
                    str(invalid),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn('"status": "failed"', result.stdout)
            self.assertIn('"code": "INSTALL_FAILED"', result.stdout)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
