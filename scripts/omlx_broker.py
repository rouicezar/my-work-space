#!/usr/bin/env python3
"""Run the product-owned loopback broker in front of oMLX."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from mac_ai_work_os.broker import (
    BrokerPolicy,
    JsonlAuditSink,
    OMLXBroker,
    OMLXUpstream,
    create_server,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=43110)
    result.add_argument("--upstream", default="http://127.0.0.1:8000")
    result.add_argument("--allowed-origin", action="append", default=[])
    result.add_argument("--max-body-bytes", type=int, default=1_048_576)
    result.add_argument("--audit-path", type=Path, required=True)
    result.add_argument("--client-token-env", default="MAC_AI_WORK_OS_BROKER_TOKEN")
    result.add_argument("--upstream-key-env", default="OMLX_API_KEY")
    return result


def required_secret(environment_name: str) -> str:
    value = os.environ.get(environment_name)
    if not value:
        raise SystemExit(f"required secret environment variable is missing: {environment_name}")
    return value


def main() -> int:
    args = parser().parse_args()
    policy = BrokerPolicy(
        client_token=required_secret(args.client_token_env),
        allowed_origins=frozenset(args.allowed_origin),
        max_body_bytes=args.max_body_bytes,
    )
    upstream = OMLXUpstream(args.upstream, required_secret(args.upstream_key_env))
    broker = OMLXBroker(policy, upstream, JsonlAuditSink(args.audit_path))
    server = create_server(args.host, args.port, broker)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
