import tempfile
import unittest
from pathlib import Path

from forma_ai.skills import (
    SkillError,
    SkillRegistry,
    discover_skills,
    format_skill_block,
    parse_frontmatter,
)
from forma_ai.skills import SkillDocument, SkillDescriptor


def write_skill(directory: Path, *, name: str, description: str, body: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "SKILL.md"
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n{body}\n",
        encoding="utf-8",
    )
    return path


class SkillDiscoveryTests(unittest.TestCase):
    def test_discover_skills_recursively_and_keep_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_skill(
                root / "nested" / "excel",
                name="excel-merge",
                description="Merge spreadsheets",
                body="SECRET BODY MUST NOT LOAD YET",
            )
            write_skill(
                root / "report",
                name="html-report",
                description="Build HTML reports",
                body="ANOTHER SECRET",
            )
            descriptors = discover_skills([root])
            self.assertEqual([item.name for item in descriptors], ["excel-merge", "html-report"])
            joined = "\n".join(item.description for item in descriptors)
            self.assertNotIn("SECRET BODY", joined)

    def test_inject_loads_only_requested_skill_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_skill(
                root / "one",
                name="alpha",
                description="First skill",
                body="# Alpha instructions",
            )
            write_skill(
                root / "two",
                name="beta",
                description="Second skill",
                body="# Beta instructions",
            )
            registry = SkillRegistry([root])
            injected = registry.inject(["beta"])
            self.assertIn('<skill name="beta"', injected)
            self.assertIn("# Beta instructions", injected)
            self.assertNotIn("Alpha instructions", injected)
            self.assertNotIn('<skill name="alpha"', injected)

    def test_parse_frontmatter_supports_quoted_description(self) -> None:
        metadata = parse_frontmatter(
            '---\nname: demo\ndescription: "Do the thing"\n---\n# Body\n'
        )
        self.assertEqual(metadata["name"], "demo")
        self.assertEqual(metadata["description"], "Do the thing")

    def test_duplicate_skill_names_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_skill(root / "a", name="dup", description="A", body="A")
            write_skill(root / "b", name="dup", description="B", body="B")
            with self.assertRaises(SkillError) as raised:
                discover_skills([root])
            self.assertEqual(raised.exception.code, "SKILL_NAME_CONFLICT")

    def test_missing_skill_on_inject_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_skill(root / "only", name="only", description="Only one", body="Body")
            registry = SkillRegistry([root])
            with self.assertRaises(SkillError) as raised:
                registry.inject(["missing"])
            self.assertEqual(raised.exception.code, "SKILL_NOT_FOUND")

    def test_format_skill_block_escapes_attributes(self) -> None:
        descriptor = SkillDescriptor(
            skill_id="fixture:demo",
            name='say-"hi"',
            description="desc",
            root=Path("/tmp/skills"),
            path=Path("/tmp/skills/demo/SKILL.md"),
        )
        block = format_skill_block(SkillDocument(descriptor=descriptor, body="# Body"))
        self.assertIn('name="say-&quot;hi&quot;"', block)


if __name__ == "__main__":
    unittest.main()
