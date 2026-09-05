import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from forma_ai.herdr_detection import prepare_herdr_detection_policy


ROOT = Path(__file__).resolve().parents[1]
QWEN_IDLE_SURFACE = """
   ▄▄▄▄▄▄  ▄▄     ▄▄ ▄▄▄▄▄▄▄ ▄▄▄    ▄▄   ┌─────────────────────────────────────────────────┐
  ██╔═══██╗██║    ██║██╔════╝████╗  ██║  │ >_ Qwen Code (v0.23.0)                          │
  ██║   ██║██║ █╗ ██║█████╗  ██╔██╗ ██║  │                                                 │
  ██║▄▄ ██║██║███╗██║██╔══╝  ██║╚██╗██║  │ API Key | Qwen3-4B-4bit (/model to change)      │
  ╚██████╔╝╚███╔███╔╝███████╗██║ ╚████║  │ /Users/.../fixture                               │
   ╚══▀▀═╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═══╝  └─────────────────────────────────────────────────┘

  Tips: You can resume a previous conversation by running qwen --continue or qwen --resume.

──────────────────────────────────────────────────────────────────────────────────────────────
>   Type your message or @path/to/file
──────────────────────────────────────────────────────────────────────────────────────────────
  ➜ fixture · Qwen3-4B-4bit
  plan mode (shift + tab to cycle)
"""


def _herdr_binary() -> Path | None:
    candidate = Path(os.environ.get(
        "FORMA_HERDR_TEST_BINARY",
        "/Users/rouice/Library/Application Support/Forma AI/cache/downloads/herdr-macos-aarch64",
    ))
    return candidate if candidate.is_file() else None


class HerdrQwenDetectionPolicyTests(unittest.TestCase):
    def test_product_policy_is_local_pinned_and_disables_remote_manifest_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "h"
            installed = prepare_herdr_detection_policy(home, repository_root=ROOT)

            self.assertEqual(installed.manifest_version, "2026.09.04.1")
            self.assertEqual(installed.manifest_sha256, installed.actual_sha256)
            self.assertIn("manifest_check = false", installed.config_path.read_text())
            self.assertIn("version_check = false", installed.config_path.read_text())
            self.assertFalse(installed.manifest_path.is_symlink())

    def test_real_herdr_explain_detects_qwen_v023_idle_surface(self):
        binary = _herdr_binary()
        if binary is None:
            self.skipTest("verified Herdr binary is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "h"
            fixture = base / "qwen-idle.txt"
            fixture.write_text(QWEN_IDLE_SURFACE, encoding="utf-8")
            prepare_herdr_detection_policy(home, repository_root=ROOT)
            environment = {
                "HOME": str(home),
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "NO_PROXY": "127.0.0.1,localhost,::1",
            }
            completed = subprocess.run(
                [str(binary), "agent", "explain", "--file", str(fixture),
                 "--agent", "qwen", "--json"],
                env=environment, capture_output=True, text=True, timeout=10,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["state"], "idle")
        self.assertEqual(Path(result["manifest_source"]), home / ".config/herdr/agent-detection/qwen.toml")
        self.assertEqual(result["manifest_version"], "2026.09.04.1")


if __name__ == "__main__":
    unittest.main()
