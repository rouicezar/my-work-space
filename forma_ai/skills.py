"""Local SKILL.md discovery and on-demand skill injection."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


SKILL_FILENAME = "SKILL.md"
MAX_SKILL_BYTES = 256 * 1024
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)
NAME_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class SkillError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SkillDescriptor:
    skill_id: str
    name: str
    description: str
    root: Path
    path: Path

    def to_catalog_entry(self) -> dict[str, str]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "path": str(self.path),
        }


@dataclass(frozen=True)
class SkillDocument:
    descriptor: SkillDescriptor
    body: str


class SkillRegistry:
    """Discover skill metadata locally and load bodies only when injected."""

    def __init__(self, roots: Iterable[Path]) -> None:
        self._roots = tuple(_normalize_roots(roots))
        self._descriptors = discover_skills(self._roots)

    @property
    def descriptors(self) -> tuple[SkillDescriptor, ...]:
        return self._descriptors

    def get(self, name: str) -> SkillDescriptor:
        for descriptor in self._descriptors:
            if descriptor.name == name:
                return descriptor
        raise SkillError("SKILL_NOT_FOUND", name)

    def load(self, name: str) -> SkillDocument:
        descriptor = self.get(name)
        body = _read_skill_body(descriptor.path)
        return SkillDocument(descriptor=descriptor, body=body)

    def inject(self, names: Iterable[str]) -> str:
        blocks: list[str] = []
        for name in names:
            document = self.load(name)
            blocks.append(format_skill_block(document))
        return "\n\n".join(blocks)


def discover_skills(roots: Iterable[Path]) -> tuple[SkillDescriptor, ...]:
    normalized_roots = _normalize_roots(roots)
    descriptors: list[SkillDescriptor] = []
    seen_names: set[str] = set()
    for root in normalized_roots:
        for directory, dirnames, filenames in os.walk(root):
            current = Path(directory)
            dirnames[:] = sorted(
                name for name in dirnames
                if not name.startswith(".") and not (current / name).is_symlink()
            )
            if SKILL_FILENAME not in filenames:
                continue
            path = current / SKILL_FILENAME
            if path.is_symlink():
                continue
            descriptor = _descriptor_from_skill_file(root=root, path=path)
            if descriptor.name in seen_names:
                raise SkillError("SKILL_NAME_CONFLICT", descriptor.name)
            seen_names.add(descriptor.name)
            descriptors.append(descriptor)
    return tuple(sorted(descriptors, key=lambda item: item.name))


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER.match(text)
    if match is None:
        raise SkillError("SKILL_FRONTMATTER_INVALID", "missing frontmatter block")
    metadata: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise SkillError("SKILL_FRONTMATTER_INVALID", line)
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if not key:
            raise SkillError("SKILL_FRONTMATTER_INVALID", line)
        metadata[key] = value
    return metadata


def format_skill_block(document: SkillDocument) -> str:
    descriptor = document.descriptor
    return (
        f'<skill name="{_escape_attr(descriptor.name)}" '
        f'path="{_escape_attr(str(descriptor.path))}">\n'
        f"{document.body.rstrip()}\n"
        "</skill>"
    )


def _descriptor_from_skill_file(*, root: Path, path: Path) -> SkillDescriptor:
    _assert_under_root(path, root)
    try:
        preview = path.read_text(encoding="utf-8", errors="strict")[:4096]
    except OSError as exc:
        raise SkillError("SKILL_READ_FAILED", str(path)) from exc
    metadata = parse_frontmatter(preview)
    name = metadata.get("name", "").strip()
    description = metadata.get("description", "").strip()
    if not name or not NAME_KEY.fullmatch(name):
        raise SkillError("SKILL_NAME_INVALID", str(path))
    if not description:
        raise SkillError("SKILL_DESCRIPTION_INVALID", str(path))
    skill_id = f"{root.name}:{name}"
    return SkillDescriptor(
        skill_id=skill_id,
        name=name,
        description=description,
        root=root,
        path=path.resolve(),
    )


def _read_skill_body(path: Path) -> str:
    if path.is_symlink():
        raise SkillError("SKILL_PATH_UNSAFE", str(path))
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SkillError("SKILL_READ_FAILED", str(path)) from exc
    if len(raw) > MAX_SKILL_BYTES:
        raise SkillError("SKILL_TOO_LARGE", str(len(raw)))
    text = raw.decode("utf-8")
    match = FRONTMATTER.match(text)
    if match is None:
        raise SkillError("SKILL_FRONTMATTER_INVALID", str(path))
    return text[match.end():].lstrip("\r\n")


def _normalize_roots(roots: Iterable[Path]) -> tuple[Path, ...]:
    normalized: list[Path] = []
    for root in roots:
        if not isinstance(root, Path) or not root.is_absolute():
            raise SkillError("SKILL_ROOT_INVALID", str(root))
        resolved = root.resolve()
        if not resolved.is_dir() or resolved.is_symlink():
            raise SkillError("SKILL_ROOT_INVALID", str(root))
        normalized.append(resolved)
    if not normalized:
        raise SkillError("SKILL_ROOT_INVALID", "at least one root is required")
    return tuple(normalized)


def _assert_under_root(path: Path, root: Path) -> None:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise SkillError("SKILL_PATH_OUTSIDE_ROOT", str(path))


def _escape_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
    )
