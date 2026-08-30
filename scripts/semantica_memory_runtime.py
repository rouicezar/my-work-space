#!/usr/bin/env python3
"""Managed-Python entrypoint for the governed Semantica memory service."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = RUNTIME_ROOT if (RUNTIME_ROOT / "mac_ai_work_os").is_dir() else RUNTIME_ROOT.parent
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mac_ai_work_os.broker import JsonlAuditSink
from mac_ai_work_os.governed_memory import GovernedMemory
from mac_ai_work_os.memory_service import GovernedMemoryService, MemoryServicePolicy, create_memory_server
from mac_ai_work_os.semantica_backend import create_managed_semantica_backend


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--memory-port", type=int, required=True)
    parser.add_argument("--omlx-port", type=int, required=True)
    parser.add_argument("--embedding-model", required=True)
    parser.add_argument("--expected-dimension", type=int, required=True)
    args = parser.parse_args()
    if not args.root.is_absolute() or not 1024 <= args.memory_port <= 65535:
        raise ValueError("unsafe memory runtime configuration")
    memory_token = os.environ.get("MAC_AI_WORK_OS_MEMORY_TOKEN", "")
    omlx_key = os.environ.get("OMLX_API_KEY", "")
    if len(memory_token) < 32 or len(omlx_key) < 32 or memory_token == omlx_key:
        raise ValueError("distinct memory and oMLX runtime secrets are required")
    backend = create_managed_semantica_backend(
        product_root=args.root, omlx_port=args.omlx_port, omlx_api_key=omlx_key,
        embedding_model=args.embedding_model, expected_dimension=args.expected_dimension,
    )
    memory = GovernedMemory(args.root, backend)
    service = GovernedMemoryService(
        MemoryServicePolicy(memory_token), memory,
        JsonlAuditSink(args.root / "logs/audit/memory-service.jsonl"),
    )
    server = create_memory_server("127.0.0.1", args.memory_port, service)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
