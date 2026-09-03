#!/usr/bin/env python3
"""Install the pinned Semantica package into an explicit product root."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.semantica_installer import (
    SemanticaInstallError,
    SemanticaInstaller,
    SemanticaInstallLayout,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, required=True, help="absolute managed product root")
    return result


def main() -> int:
    args = parser().parse_args()
    if not args.root.is_absolute():
        print(json.dumps({"status": "failed", "code": "ROOT_NOT_ABSOLUTE"}))
        return 2
    try:
        active = SemanticaInstaller(SemanticaInstallLayout(args.root)).install()
    except Exception as exc:
        code = exc.code if isinstance(exc, SemanticaInstallError) else "INSTALL_FAILED"
        print(json.dumps({"status": "failed", "code": code, "message": str(exc)}))
        return 2
    print(json.dumps({"status": "installed", "active": active}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
