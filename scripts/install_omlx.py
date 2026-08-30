#!/usr/bin/env python3
"""Install the pinned oMLX artifact into an explicit product root."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.artifacts import load_component, select_artifact
from forma_ai.downloads import ResumableDownloader
from forma_ai.installer import InstallError, OMLXInstallLayout, OMLXInstaller


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, required=True, help="absolute managed product root")
    result.add_argument("--os-major", type=int, required=True)
    result.add_argument(
        "--upstreams",
        type=Path,
        default=REPOSITORY_ROOT / "config/upstreams.json",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    if not args.root.is_absolute():
        print(json.dumps({"status": "failed", "code": "ROOT_NOT_ABSOLUTE"}))
        return 2
    try:
        component = load_component(args.upstreams, "omlx")
        expected = select_artifact(component, platform="macos", os_major=args.os_major)
        installer = OMLXInstaller(
            OMLXInstallLayout(args.root),
            expected,
            downloader=ResumableDownloader(),
        )
        active = installer.run()
    except Exception as exc:
        code = exc.code if isinstance(exc, InstallError) else "INSTALL_FAILED"
        print(json.dumps({"status": "failed", "code": code, "message": str(exc)}))
        return 2
    print(json.dumps({"status": "installed", "active": asdict(active)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
