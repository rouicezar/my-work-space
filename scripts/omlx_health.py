#!/usr/bin/env python3
"""Emit a machine-readable oMLX health report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.adapters.omlx import OMLXAdapter, UrllibTransport, detect_installation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--api-key-env", default="OMLX_API_KEY")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(args.api_key_env)
    adapter = OMLXAdapter(UrllibTransport(args.base_url, api_key=api_key, timeout=args.timeout))
    report = adapter.probe(detect_installation(), deep=args.deep, model=args.model)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0 if report.status == "ready" else 1 if report.status in {"healthy_no_models", "shallow_ready"} else 2


if __name__ == "__main__":
    sys.exit(main())
