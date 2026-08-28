#!/usr/bin/env python3
"""Inspect a macOS app's plist, architecture, signature, and Gatekeeper status."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from mac_ai_work_os.macos_bundle import inspect_app


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    result = inspect_app(args.app, args.expected_version)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.valid else 2


if __name__ == "__main__":
    sys.exit(main())
