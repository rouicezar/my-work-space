import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from forma_ai.artifacts import (
    ArtifactError,
    ArtifactExpectation,
    load_component,
    select_artifact,
    verify_file,
)


ROOT = Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    def test_selects_macos_26_27_omlx_artifact(self):
        component = load_component(ROOT / "config/upstreams.json", "omlx")
        selected = select_artifact(component, platform="macos", os_major=26)
        self.assertEqual(selected.artifact_id, "macos-26-27")
        self.assertEqual(selected.size_bytes, 807057789)

    def test_selects_herdr_aarch64_artifact_by_architecture(self):
        component = load_component(ROOT / "config/upstreams.json", "herdr")
        selected = select_artifact(
            component, platform="macos", os_major=26, architecture="aarch64"
        )
        self.assertEqual(selected.artifact_id, "macos-aarch64")
        self.assertEqual(selected.size_bytes, 18969952)
        self.assertEqual(
            selected.sha256,
            "a5d4f4d504d8b309c91f811050559300faba31258425f53c50852fc96f6ae574",
        )
        self.assertEqual(
            selected.url,
            "https://github.com/herdrdev/herdr/releases/download/v0.8.2/herdr-macos-aarch64",
        )

    def test_selects_herdr_x86_64_artifact_by_architecture(self):
        component = load_component(ROOT / "config/upstreams.json", "herdr")
        selected = select_artifact(
            component, platform="macos", os_major=26, architecture="x86_64"
        )
        self.assertEqual(selected.artifact_id, "macos-x86_64")
        self.assertEqual(selected.size_bytes, 20551504)
        self.assertEqual(
            selected.sha256,
            "ab50262c8190cd7aa9056d249d255c08c328c3e8716de9cfa29db4f131b8e2c1",
        )

    def test_herdr_selection_requires_an_architecture_discriminator(self):
        component = load_component(ROOT / "config/upstreams.json", "herdr")
        with self.assertRaisesRegex(ArtifactError, "got 0"):
            select_artifact(component, platform="macos", os_major=26)

    def test_unknown_architecture_has_no_silent_fallback(self):
        component = load_component(ROOT / "config/upstreams.json", "herdr")
        with self.assertRaisesRegex(ArtifactError, "got 0"):
            select_artifact(
                component, platform="macos", os_major=26, architecture="riscv64"
            )

    def test_herdr_artifact_is_not_macos_version_gated(self):
        component = load_component(ROOT / "config/upstreams.json", "herdr")
        selected = select_artifact(
            component, platform="macos", os_major=14, architecture="aarch64"
        )
        self.assertEqual(selected.artifact_id, "macos-aarch64")

    def test_macos_16_has_no_silent_fallback(self):
        component = load_component(ROOT / "config/upstreams.json", "omlx")
        with self.assertRaisesRegex(ArtifactError, "got 0"):
            select_artifact(component, platform="macos", os_major=16)

    def test_valid_file_matches_size_and_digest(self):
        payload = b"verified artifact fixture"
        expected = ArtifactExpectation(
            component="fixture",
            release="v1.0.0",
            artifact_id="fixture",
            name="fixture.bin",
            size_bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            url="https://github.com/example/project/releases/download/v1.0.0/fixture.bin",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / expected.name
            path.write_bytes(payload)
            result = verify_file(path, expected, chunk_size=3)
        self.assertTrue(result.valid)
        self.assertTrue(result.size_matches)
        self.assertTrue(result.digest_matches)

    def test_tampered_file_is_rejected(self):
        payload = b"expected"
        expected = ArtifactExpectation(
            component="fixture",
            release="v1.0.0",
            artifact_id="fixture",
            name="fixture.bin",
            size_bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            url="https://github.com/example/project/releases/download/v1.0.0/fixture.bin",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / expected.name
            path.write_bytes(b"tampered")
            result = verify_file(path, expected)
        self.assertFalse(result.valid)
        self.assertFalse(result.digest_matches)

    def test_upstream_manifest_remains_valid_json(self):
        data = json.loads((ROOT / "config/upstreams.json").read_text())
        self.assertEqual(data["schema_version"], 1)

    def test_artifact_name_cannot_escape_download_directory(self):
        component = load_component(ROOT / "config/upstreams.json", "omlx")
        component["artifacts"][1]["name"] = "../escape.dmg"
        with self.assertRaisesRegex(ArtifactError, "plain filename"):
            select_artifact(component, platform="macos", os_major=26)


if __name__ == "__main__":
    unittest.main()
