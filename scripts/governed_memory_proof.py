#!/usr/bin/env python3
"""P7-T05 acceptance command: prove governed memory workflow on managed Semantica."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.governed_memory_proof import run_governed_memory_proof


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="absolute managed product root")
    parser.add_argument("--work-root", type=Path, default=None, help="optional isolated proof work root")
    args = parser.parse_args()
    if not args.root.is_absolute():
        raise SystemExit("--root must be an absolute path")
    if args.work_root is not None and not args.work_root.is_absolute():
        raise SystemExit("--work-root must be an absolute path")
    evidence = run_governed_memory_proof(
        args.root,
        work_root=args.work_root,
        repository_root=REPOSITORY_ROOT,
    )
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence.get("status") == "proof_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
