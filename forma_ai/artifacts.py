"""Artifact selection and integrity verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ArtifactError(ValueError):
    """Artifact metadata is missing, ambiguous, or unsafe."""


@dataclass(frozen=True)
class ArtifactExpectation:
    component: str
    release: str
    artifact_id: str
    name: str
    size_bytes: int
    sha256: str
    url: str


@dataclass(frozen=True)
class ArtifactVerification:
    schema_version: int
    component: str
    release: str
    artifact_id: str
    path: str
    expected_size_bytes: int
    actual_size_bytes: int
    expected_sha256: str
    actual_sha256: str
    size_matches: bool
    digest_matches: bool
    valid: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_component(path: Path, component_id: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    components = [item for item in data.get("components", []) if item.get("id") == component_id]
    if len(components) != 1:
        raise ArtifactError(f"expected exactly one component {component_id!r}")
    return components[0]


def select_artifact(component: dict[str, Any], *, platform: str, os_major: int) -> ArtifactExpectation:
    matches = [
        item
        for item in component.get("artifacts", [])
        if item.get("platform") == platform
        and int(item.get("minimum_macos_major", -1)) <= os_major
        and os_major <= int(item.get("maximum_macos_major", -1))
    ]
    if len(matches) != 1:
        raise ArtifactError(
            f"expected exactly one {component.get('id')} artifact for {platform} {os_major}, got {len(matches)}"
        )
    item = matches[0]
    digest = str(item.get("sha256", ""))
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ArtifactError("artifact sha256 must be 64 lowercase hexadecimal characters")
    size = item.get("size_bytes")
    if not isinstance(size, int) or size <= 0:
        raise ArtifactError("artifact size must be a positive integer")
    parsed = urlparse(str(item.get("url", "")))
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise ArtifactError("artifact URL must use https://github.com")
    name = str(item.get("name", ""))
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ArtifactError("artifact name must be a plain filename")
    return ArtifactExpectation(
        component=component["id"],
        release=component["release"],
        artifact_id=item["id"],
        name=name,
        size_bytes=size,
        sha256=digest,
        url=item["url"],
    )


def verify_file(path: Path, expected: ArtifactExpectation, chunk_size: int = 1024 * 1024) -> ArtifactVerification:
    if chunk_size <= 0:
        raise ArtifactError("chunk_size must be positive")
    digest = hashlib.sha256()
    actual_size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            actual_size += len(chunk)
            digest.update(chunk)
    actual_digest = digest.hexdigest()
    size_matches = actual_size == expected.size_bytes
    digest_matches = actual_digest == expected.sha256
    return ArtifactVerification(
        schema_version=1,
        component=expected.component,
        release=expected.release,
        artifact_id=expected.artifact_id,
        path=str(path),
        expected_size_bytes=expected.size_bytes,
        actual_size_bytes=actual_size,
        expected_sha256=expected.sha256,
        actual_sha256=actual_digest,
        size_matches=size_matches,
        digest_matches=digest_matches,
        valid=size_matches and digest_matches,
    )
