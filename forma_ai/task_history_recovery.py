"""Revision-checked task history recovery over Herdr lifecycle authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forma_ai.herdr_adapter import HerdrAdapter, HerdrTask
from forma_ai.herdr_presentation import HerdrPresentedAgent
from forma_ai.task_metadata_projection import ProjectedTaskView, TaskMetadataRecord
from forma_ai.task_metadata_reconcile import (
    build_reconcile_payload,
    find_linked_agent,
    obtain_herdr_reconcile_snapshot,
    projected_view_to_dict,
    reconcile_task_view,
)
from forma_ai.task_metadata_store import TaskMetadataStore, TaskMetadataStoreError


CANCELLABLE_RUNTIME_STATES = frozenset({"running", "starting", "blocked", "queued"})


class TaskHistoryRecoveryError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RecoveryContext:
    metadata: TaskMetadataRecord
    view: ProjectedTaskView
    agent: HerdrPresentedAgent


def binding_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "runtime_authority": "herdr",
        "recovery_actions": {
            "reclaim": "task-history-reclaim",
            "cancel": "task-history-cancel",
            "fresh_run": "task-history-fresh-run",
        },
        "requires_fresh_reconcile": True,
        "requires_matching_revision": True,
    }


def herdr_task_from_projection(
    metadata: TaskMetadataRecord,
    agent: HerdrPresentedAgent,
) -> HerdrTask:
    if not metadata.run_id:
        raise TaskHistoryRecoveryError("METADATA_RUN_ID_MISSING", "run_id is required for recovery")
    return HerdrTask(
        task_id=metadata.task_id,
        run_id=metadata.run_id,
        workspace_id=agent.workspace_id,
        pane_id=agent.pane_id,
        terminal_id=agent.terminal_id,
        state=HerdrAdapter._task_state(agent.state),
        revision=agent.revision,
    )


def load_recovery_context(
    product_root,
    task_id: str,
    *,
    runtime_status,
    snapshot_source,
) -> RecoveryContext:
    metadata = TaskMetadataStore(product_root).load(task_id)
    reconcile = obtain_herdr_reconcile_snapshot(
        runtime_status=runtime_status,
        snapshot_source=snapshot_source,
    )
    view = reconcile_task_view(metadata, reconcile)
    agent = find_linked_agent(metadata, reconcile.agents)
    if agent is None:
        raise TaskHistoryRecoveryError(
            "RECOVERY_AGENT_MISSING",
            "no linked Herdr agent for persisted metadata",
        )
    return RecoveryContext(metadata=metadata, view=view, agent=agent)


def validate_reclaim_eligibility(context: RecoveryContext) -> None:
    if context.view.freshness != "fresh":
        raise TaskHistoryRecoveryError("RECOVERY_STALE_SNAPSHOT", "fresh Herdr snapshot required")
    if context.view.reconciliation_required:
        raise TaskHistoryRecoveryError("RECOVERY_RECONCILIATION_REQUIRED", "task must be reconciled first")
    if not context.view.may_resume:
        raise TaskHistoryRecoveryError("RECOVERY_NOT_RESUMABLE", "task is not eligible for reclaim")


def validate_cancel_eligibility(context: RecoveryContext, *, expected_revision: int) -> None:
    if context.view.freshness != "fresh":
        raise TaskHistoryRecoveryError("RECOVERY_STALE_SNAPSHOT", "fresh Herdr snapshot required")
    if context.view.reconciliation_required:
        raise TaskHistoryRecoveryError("RECOVERY_RECONCILIATION_REQUIRED", "task must be reconciled first")
    if context.agent.revision != expected_revision:
        raise TaskHistoryRecoveryError("RECOVERY_REVISION_MISMATCH", "expected revision does not match Herdr")
    if context.view.runtime_state not in CANCELLABLE_RUNTIME_STATES:
        raise TaskHistoryRecoveryError("RECOVERY_NOT_CANCELLABLE", "task is not in a cancellable runtime state")


def validate_fresh_run_eligibility(
    context: RecoveryContext,
    *,
    fresh_pane_id: str,
) -> None:
    if context.view.freshness != "fresh":
        raise TaskHistoryRecoveryError("RECOVERY_STALE_SNAPSHOT", "fresh Herdr snapshot required")
    if context.view.reconciliation_required:
        raise TaskHistoryRecoveryError("RECOVERY_RECONCILIATION_REQUIRED", "task must be reconciled first")
    if not fresh_pane_id or fresh_pane_id == context.metadata.herdr_pane_id:
        raise TaskHistoryRecoveryError("RECOVERY_FRESH_PANE_REQUIRED", "fresh run requires a different pane")


def execute_reclaim(context: RecoveryContext, adapter: HerdrAdapter) -> dict[str, Any]:
    validate_reclaim_eligibility(context)
    task = herdr_task_from_projection(context.metadata, context.agent)
    reclaimed = adapter.reclaim_task(task=task)
    return {
        "action": "reclaim",
        "task_id": reclaimed.task_id,
        "run_id": reclaimed.run_id,
        "pane_id": reclaimed.pane_id,
        "revision": reclaimed.revision,
        "state": reclaimed.state,
    }


def execute_cancel(
    context: RecoveryContext,
    adapter: HerdrAdapter,
    *,
    expected_revision: int,
    correlation_id: str,
) -> dict[str, Any]:
    validate_cancel_eligibility(context, expected_revision=expected_revision)
    task = herdr_task_from_projection(context.metadata, context.agent)
    adapter.reclaim_task(task=task)
    result = adapter.cancel_task(
        run_id=task.run_id,
        correlation_id=correlation_id,
        expected_revision=expected_revision,
    )
    return {
        "action": result.action,
        "task_id": result.task_id,
        "run_id": result.run_id,
        "revision": result.revision,
        "state": result.state,
    }


def execute_fresh_run(
    context: RecoveryContext,
    adapter: HerdrAdapter,
    *,
    fresh_pane_id: str,
    correlation_id: str,
    agent_name: str = "forma-recovery",
    agent_kind: str = "assistant",
) -> dict[str, Any]:
    validate_fresh_run_eligibility(context, fresh_pane_id=fresh_pane_id)
    previous = herdr_task_from_projection(context.metadata, context.agent)
    adapter.reclaim_task(task=previous)
    fresh = adapter.start_fresh_task(
        previous_task=previous,
        correlation_id=correlation_id,
        agent_name=agent_name,
        agent_kind=agent_kind,
        pane_id=fresh_pane_id,
    )
    return {
        "action": "fresh_run",
        "task_id": fresh.task_id,
        "run_id": fresh.run_id,
        "pane_id": fresh.pane_id,
        "revision": fresh.revision,
        "state": fresh.state,
    }


def build_history_snapshot(
    product_root,
    *,
    task_id: str | None = None,
    runtime_status,
    snapshot_source,
) -> dict[str, Any]:
    payload = build_reconcile_payload(
        product_root,
        task_id=task_id,
        runtime_status=runtime_status,
        snapshot_source=snapshot_source,
    )
    available_pane_ids: list[str] = []
    if snapshot_source is not None and payload.get("freshness") == "fresh":
        try:
            snapshot = snapshot_source.snapshot()
            available_pane_ids = sorted({pane.pane_id for pane in snapshot.panes})
        except Exception:
            available_pane_ids = []
    payload["available_pane_ids"] = available_pane_ids
    payload["binding"] = binding_contract()
    return payload
