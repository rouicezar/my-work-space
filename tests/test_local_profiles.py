import json
import tempfile
import unittest
from pathlib import Path

from forma_ai.local_profiles import LocalProfileError, load_local_profile


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ID = "qwen3-4b-4bit-apple-silicon-alpha"


class LocalProfileCatalogTests(unittest.TestCase):
    def load(self, path=ROOT / "config/local-model-profiles.json"):
        return load_local_profile(
            path, PROFILE_ID, known_model_ids=frozenset({
                "qwen3-0.6b-4bit-alpha", "qwen3-8b-4bit-alpha", "qwen3-4b-4bit-alpha",
            }),
            known_hardware_profile_ids=frozenset({
                "apple-silicon-16gb", "apple-silicon-32gb", "apple-silicon-64gb",
            }), repository_root=ROOT,
        )

    def test_real_profile_is_evidence_bound_and_conservative(self):
        profile = self.load()
        self.assertEqual(profile.capabilities, frozenset({"chat", "tools"}))
        self.assertEqual(profile.runtime_model_ids, frozenset({"Qwen3-4B-4bit"}))
        self.assertEqual(profile.context_window_tokens, 512)
        self.assertEqual(profile.maximum_output_tokens, 64)
        self.assertEqual(profile.evidence_status, "verified_single_machine")
        self.assertTrue((ROOT / profile.evidence_path).is_file())

    def test_profile_capabilities_are_declared_by_its_model_definition(self):
        profiles = json.loads((ROOT / "config/local-model-profiles.json").read_text())
        models = json.loads((ROOT / "config/models.json").read_text())
        model_capabilities = {
            item["id"]: frozenset(item["capabilities"])
            for item in models["models"]
        }
        for profile in profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                self.assertTrue(
                    frozenset(profile["capabilities"]).issubset(
                        model_capabilities[profile["model_definition_id"]]
                    )
                )

    def test_unknown_model_hardware_capability_and_missing_evidence_fail(self):
        source = json.loads((ROOT / "config/local-model-profiles.json").read_text())
        mutations = (
            ("model_definition_id", "unknown", "LOCAL_PROFILE_MODEL_UNKNOWN"),
            ("hardware_profile_ids", ["unknown"], "LOCAL_PROFILE_HARDWARE_UNKNOWN"),
            ("capabilities", ["magic"], "LOCAL_PROFILE_CAPABILITIES_INVALID"),
            ("evidence_path", "evidence/missing.md", "LOCAL_PROFILE_EVIDENCE_MISSING"),
        )
        for field, value, code in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                copy = json.loads(json.dumps(source))
                selected = next(
                    item for item in copy["profiles"] if item["id"] == PROFILE_ID
                )
                selected[field] = value
                path = Path(directory) / "profiles.json"
                path.write_text(json.dumps(copy), encoding="utf-8")
                with self.assertRaises(LocalProfileError) as raised:
                    self.load(path)
                self.assertEqual(raised.exception.code, code)


if __name__ == "__main__":
    unittest.main()
