"""P9-T01 public distribution checklist contract tests."""

import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = REPOSITORY_ROOT / "docs/distribution/public-release-checklist.md"

REQUIRED_SECTIONS = (
    "Gate A — Product identity and legal readiness",
    "Gate B — Upstream redistribution and notices",
    "Gate C — Secrets, credentials, and private development isolation",
    "Gate D — Install, upgrade, rollback, uninstall, recovery",
    "Gate E — Runtime, security, and policy behavior",
    "Gate F — Quality, accessibility, usability, and novice acceptance",
    "Gate G — Release packaging and publication",
    "Release sign-off",
    "P9 task cross-reference",
)

REQUIRED_UPSTREAM_IDS = ("Semantica", "Herdr", "oMLX", "holaOS")


class PublicReleaseChecklistTests(unittest.TestCase):
    def test_checklist_file_exists(self):
        self.assertTrue(CHECKLIST.is_file(), "public release checklist must exist")

    def test_checklist_declares_required_gates(self):
        text = CHECKLIST.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_checklist_covers_all_four_upstreams(self):
        text = CHECKLIST.read_text(encoding="utf-8")
        for upstream in REQUIRED_UPSTREAM_IDS:
            with self.subTest(upstream=upstream):
                self.assertIn(upstream, text)

    def test_checklist_references_upstreams_manifest(self):
        text = CHECKLIST.read_text(encoding="utf-8")
        self.assertIn("config/upstreams.json", text)

    def test_checklist_states_existence_is_not_pass(self):
        text = CHECKLIST.read_text(encoding="utf-8")
        self.assertIn("not automatic evidence of pass", text)


if __name__ == "__main__":
    unittest.main()
