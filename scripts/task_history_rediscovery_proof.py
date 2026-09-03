#!/usr/bin/env python3
"""P8-T05 acceptance command: prove task rediscovery after reopen and Herdr reconnect."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.task_history_rediscovery import run_rediscovery_proof, multi_agent_snapshot
from forma_ai.task_metadata_projection import TaskMetadataRecord
from unittest.mock import Mock
from forma_ai.herdr_adapter import HerdrTask


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="absolute managed product root")
    args = parser.parse_args()
    if not args.root.is_absolute():
        raise SystemExit("--root must be an absolute path")

    snapshot_source = Mock()
    snapshot_source.snapshot.return_value = multi_agent_snapshot(
        {
            "terminal_id": "terminal-1",
            "agent_status": "done",
            "workspace_id": "workspace-1",
            "tab_id": "tab-1",
            "pane_id": "pane-1",
            "focused": True,
            "revision": 9,
        },
        {
            "terminal_id": "terminal-2",
            "agent_status": "blocked",
            "workspace_id": "workspace-1",
            "tab_id": "tab-1",
            "pane_id": "pane-2",
            "focused": False,
            "revision": 5,
        },
    )
    adapter = Mock()
    adapter.reclaim_task.return_value = HerdrTask(
        task_id="task-2", run_id="run-2", workspace_id="workspace-1",
        pane_id="pane-2", terminal_id="terminal-2", state="blocked", revision=5,
    )
    evidence = run_rediscovery_proof(
        args.root,
        records=(
            TaskMetadataRecord(
                task_id="task-1",
                correlation_id="corr-1",
                intent_label="Proof task A",
                recorded_at="2026-09-04T00:00:00+00:00",
                updated_at="2026-09-04T00:00:00+00:00",
                run_id="run-1",
                herdr_pane_id="pane-1",
                last_accepted_revision=8,
            ),
            TaskMetadataRecord(
                task_id="task-2",
                correlation_id="corr-2",
                intent_label="Proof task B",
                recorded_at="2026-09-04T00:00:00+00:00",
                updated_at="2026-09-04T00:00:00+00:00",
                run_id="run-2",
                herdr_pane_id="pane-2",
                last_accepted_revision=4,
            ),
        ),
        detached_status=lambda: {"herdr_alive": False},
        reconnected_status=lambda: {"herdr_alive": True},
        reconnected_snapshot_source=snapshot_source,
        reclaim_adapter=adapter,
    )
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence.get("status") == "proof_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
