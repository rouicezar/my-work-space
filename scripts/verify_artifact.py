#!/usr/bin/env python3
"""Select and verify a pinned upstream release artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.artifacts import ArtifactError, load_component, select_artifact, verify_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--platform", default="macos")
    parser.add_argument("--os-major", type=int, required=True)
    parser.add_argument("--manifest", type=Path, default=REPOSITORY_ROOT / "config/upstreams.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        component = load_component(args.manifest, args.component)
        expected = select_artifact(component, platform=args.platform, os_major=args.os_major)
        result = verify_file(args.artifact, expected)
    except (ArtifactError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_version": 1, "status": "error", "error": str(exc)}))
        return 3
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.valid else 2


if __name__ == "__main__":
    sys.exit(main())
