"""Read-only macOS application bundle inspection."""

from __future__ import annotations

import plistlib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


@dataclass(frozen=True)
class CommandEvidence:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class AppInspection:
    schema_version: int
    path: str
    bundle_identifier: str | None
    short_version: str | None
    build_version: str | None
    minimum_macos: str | None
    executable: str | None
    architectures: list[str]
    codesign_valid: bool
    gatekeeper_accepted: bool
    expected_version: str
    version_matches: bool
    arm64_supported: bool
    valid: bool
    evidence: dict[str, Any]
    errors: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


Runner = Callable[[Sequence[str]], CommandEvidence]


def run_command(args: Sequence[str]) -> CommandEvidence:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return CommandEvidence(list(args), result.returncode, result.stdout.strip(), result.stderr.strip())


def inspect_app(app: Path, expected_version: str, runner: Runner = run_command) -> AppInspection:
    errors: list[dict[str, str]] = []
    info_path = app / "Contents/Info.plist"
    try:
        with info_path.open("rb") as handle:
            info = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as exc:
        info = {}
        errors.append({"code": "INVALID_PLIST", "message": str(exc)})

    executable_name = info.get("CFBundleExecutable")
    executable_path = app / "Contents/MacOS" / executable_name if isinstance(executable_name, str) else None
    if executable_path is None or not executable_path.is_file():
        errors.append({"code": "MISSING_EXECUTABLE", "message": str(executable_path or "unknown")})

    lipo = runner(["/usr/bin/lipo", "-archs", str(executable_path)]) if executable_path else None
    architectures = lipo.stdout.split() if lipo and lipo.returncode == 0 else []
    if lipo and lipo.returncode != 0:
        errors.append({"code": "ARCH_INSPECTION_FAILED", "message": lipo.stderr or lipo.stdout})

    codesign = runner(["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app)])
    if codesign.returncode != 0:
        errors.append({"code": "CODESIGN_INVALID", "message": codesign.stderr or codesign.stdout})

    details = runner(["/usr/bin/codesign", "-d", "--verbose=4", str(app)])
    gatekeeper = runner(["/usr/sbin/spctl", "-a", "-vv", "-t", "exec", str(app)])
    if gatekeeper.returncode != 0:
        errors.append({"code": "GATEKEEPER_REJECTED", "message": gatekeeper.stderr or gatekeeper.stdout})

    short_version = info.get("CFBundleShortVersionString")
    version_matches = short_version == expected_version
    if not version_matches:
        errors.append(
            {"code": "VERSION_MISMATCH", "message": f"expected {expected_version}, got {short_version}"}
        )
    arm64_supported = "arm64" in architectures or "arm64e" in architectures
    if not arm64_supported:
        errors.append({"code": "ARM64_MISSING", "message": f"architectures: {architectures}"})

    return AppInspection(
        schema_version=1,
        path=str(app),
        bundle_identifier=info.get("CFBundleIdentifier"),
        short_version=short_version,
        build_version=info.get("CFBundleVersion"),
        minimum_macos=info.get("LSMinimumSystemVersion"),
        executable=executable_name,
        architectures=architectures,
        codesign_valid=codesign.returncode == 0,
        gatekeeper_accepted=gatekeeper.returncode == 0,
        expected_version=expected_version,
        version_matches=version_matches,
        arm64_supported=arm64_supported,
        valid=not errors,
        evidence={
            "lipo": asdict(lipo) if lipo else None,
            "codesign_verify": asdict(codesign),
            "codesign_details": asdict(details),
            "gatekeeper": asdict(gatekeeper),
        },
        errors=errors,
    )
