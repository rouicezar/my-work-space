"""Pinned product policy for Herdr screen-manifest detection."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


PINNED_QWEN_MANIFEST_VERSION = "2026.09.04.1"
PINNED_QWEN_MANIFEST = br'''id = "qwen"
version = "2026.09.04.1"
min_engine_version = 2
updated_at = "2026-09-04T00:00:00Z"
aliases = ["qwen-code", "qwen code"]

[[rules]]
id = "osc_title_blocked"
state = "blocked"
priority = 1200
region = "osc_title"
visible_blocker = true
regex = ['^\x{2733}\x{FE0E}? ']

[[rules]]
id = "osc_title_working"
state = "working"
priority = 1100
region = "osc_title"
visible_working = true
regex = ['^\x{25D0}\x{FE0E}? ']

[[rules]]
id = "tool_confirmation"
state = "blocked"
priority = 990
region = "bottom_non_empty_lines(20)"
visible_blocker = true
regex = ['(?i)waiting for user confirmation', '(?i)yes, allow once', '(?i)do you want to proceed']

[[rules]]
id = "cancel_hint_working"
state = "working"
priority = 900
region = "bottom_non_empty_lines(8)"
visible_working = true
line_regex = ['(?i)^\s*(?:[\x{2801}-\x{28ff}]|\.{1,2})\s+.*\(\d+(?:m(?:\s+\d+s)?|s).*esc to cancel\)\s*$']

[[rules]]
id = "composer_idle_v023"
state = "idle"
priority = 100
region = "bottom_non_empty_lines(30)"
visible_idle = true
line_regex = ['(?i)^\s*>\s*(?:type\s*)?.*$']
any = [
  { regex = ['(?i)type your message'] },
  { regex = ['(?i)your message or @path/to/file'] },
  { contains = ["@path/to/file"] },
]
'''
PINNED_QWEN_MANIFEST_SHA256 = "26e511f26a62d9123409c32ad3235a015329690c9373aff8fc86cd44262a91a2"
HERDR_CONFIG = b'''[update]
version_check = false
manifest_check = false
'''


class HerdrDetectionPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class InstalledHerdrDetectionPolicy:
    manifest_version: str
    manifest_sha256: str
    actual_sha256: str
    manifest_path: Path
    config_path: Path


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise HerdrDetectionPolicyError(f"unsafe Herdr policy destination: {path}")
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    temporary = Path(name)
    os.fchmod(descriptor, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def prepare_herdr_detection_policy(
    home: Path, *, repository_root: Path | None = None,
) -> InstalledHerdrDetectionPolicy:
    if not home.is_absolute():
        raise HerdrDetectionPolicyError("Herdr HOME must be absolute")
    actual = hashlib.sha256(PINNED_QWEN_MANIFEST).hexdigest()
    if actual != PINNED_QWEN_MANIFEST_SHA256:
        raise HerdrDetectionPolicyError("pinned Qwen manifest digest mismatch")
    config_root = home / ".config" / "herdr"
    manifest_path = config_root / "agent-detection" / "qwen.toml"
    config_path = config_root / "config.toml"
    _atomic_write(manifest_path, PINNED_QWEN_MANIFEST)
    _atomic_write(config_path, HERDR_CONFIG)
    _ = repository_root
    return InstalledHerdrDetectionPolicy(
        manifest_version=PINNED_QWEN_MANIFEST_VERSION,
        manifest_sha256=PINNED_QWEN_MANIFEST_SHA256,
        actual_sha256=actual,
        manifest_path=manifest_path,
        config_path=config_path,
    )
