#!/usr/bin/env python3
"""Prove managed Semantica lifecycle inside the pinned runtime.

This is the P7-T03 acceptance command. It verifies the managed installation,
runs one store/save/reload/retrieve/forget cycle through the pinned
``AgentContext`` surface, and records honest evidence. When oMLX embedding
parameters are supplied and the probe succeeds, the cycle uses the real local
embedding boundary; otherwise it uses an explicit no-network fixture boundary.

The oMLX API key is read only from the environment name supplied by
``--api-key-env`` (default ``OMLX_API_KEY``) and is never printed or logged.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.semantica_runtime_proof import redact_proof_evidence, run_semantica_runtime_proof


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="absolute managed product root")
    parser.add_argument("--omlx-port", type=int, default=None)
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--expected-dimension", type=int, default=None)
    parser.add_argument("--api-key-env", default="OMLX_API_KEY")
    args = parser.parse_args()

    if not args.root.is_absolute():
        raise SystemExit("--root must be an absolute path")

    omlx_api_key = None
    if args.omlx_port is not None or args.embedding_model:
        omlx_api_key = os.environ.get(args.api_key_env, "")
        if len(omlx_api_key) < 32:
            raise SystemExit(f"a >=32-character local API key is required via {args.api_key_env}")

    evidence = run_semantica_runtime_proof(
        args.root,
        omlx_port=args.omlx_port,
        omlx_api_key=omlx_api_key,
        embedding_model=args.embedding_model,
        expected_dimension=args.expected_dimension,
        repository_root=REPOSITORY_ROOT,
    )
    safe = redact_proof_evidence(evidence)
    print(json.dumps(safe, ensure_ascii=False, indent=2))
    return 0 if evidence.get("status") == "proof_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
