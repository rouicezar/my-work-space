#!/usr/bin/env python3
"""Record interrupted-task manual recovery proof evidence for P8-T06."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import Mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.herdr_adapter import HerdrTask
from forma_ai.task_history_manual_proof import (
    build_recovery_evidence_payload,
    render_recovery_evidence_markdown,
)
from forma_ai.task_history_rediscovery import multi_agent_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="absolute product root")
    parser.add_argument("--date", default=date.today().isoformat(), help="evidence date YYYY-MM-DD")
    parser.add_argument("--output", type=Path, default=None, help="optional evidence path override")
    args = parser.parse_args()
    if not args.root.is_absolute():
        raise SystemExit("--root must be an absolute path")

    snapshot_source = Mock()
    snapshot_source.snapshot.return_value = multi_agent_snapshot(
        {
            "terminal_id": "terminal-interrupted-1",
            "agent_status": "blocked",
            "workspace_id": "workspace-1",
            "tab_id": "tab-1",
            "pane_id": "pane-interrupted-1",
            "focused": True,
            "revision": 7,
        },
    )
    adapter = Mock()
    adapter.reclaim_task.return_value = HerdrTask(
        task_id="task-interrupted-1",
        run_id="run-interrupted-1",
        workspace_id="workspace-1",
        pane_id="pane-interrupted-1",
        terminal_id="terminal-interrupted-1",
        state="blocked",
        revision=7,
    )

    payload = build_recovery_evidence_payload(
        args.root,
        detached_status=lambda: {"herdr_alive": False},
        reconnected_status=lambda: {"herdr_alive": True},
        reconnected_snapshot_source=snapshot_source,
        reclaim_adapter=adapter,
    )
    markdown = render_recovery_evidence_markdown(payload, proof_date=args.date)
    output = args.output or (
        REPOSITORY_ROOT / f"evidence/recovery/recovery-{args.date}.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(json.dumps({"written": str(output), **payload["evaluation"]}, ensure_ascii=False, indent=2))
    return 0 if payload["evaluation"].get("status") == "proof_recorded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
