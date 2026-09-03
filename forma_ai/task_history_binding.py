"""Supervisor binding for reconciled task history projection over Herdr authority."""

from __future__ import annotations

from typing import Any

from forma_ai.task_metadata_reconcile import build_reconcile_payload


TASK_HISTORY_AUDIT_PATH = "logs/audit/task-history-reconcile.jsonl"

SUPERVISOR_COMMANDS = {
    "reconcile": "task-metadata-reconcile",
}


def build_history_reconcile_snapshot(product_root, *, task_id: str | None = None) -> dict[str, Any]:
    return build_reconcile_payload(product_root, task_id=task_id)
