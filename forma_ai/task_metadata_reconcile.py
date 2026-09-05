"""Reconcile persisted task metadata against fresh Herdr snapshot authority."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from forma_ai.herdr_adapter import HerdrAdapter, HerdrSessionAgent, HerdrSessionSnapshot
from forma_ai.herdr_presentation import HerdrPresentedAgent
from forma_ai.runtime import RuntimeManager
from forma_ai.task_metadata_projection import (
    RUNTIME_AUTHORITY,
    ProjectedTaskView,
    TaskMetadataRecord,
    project_task_view,
)
from forma_ai.task_metadata_store import TaskMetadataStore


class HerdrSnapshotSource(Protocol):
    def snapshot(self) -> HerdrSessionSnapshot: ...


RuntimeStatus = Callable[[], dict[str, object]]


@dataclass(frozen=True)
class HerdrReconcileSnapshot:
    freshness: str
    reason: str | None
    agents: tuple[HerdrPresentedAgent, ...]
    herdr_version: str | None = None
    herdr_protocol: int | None = None


def presented_agent_from_session(agent: HerdrSessionAgent) -> HerdrPresentedAgent:
    return HerdrPresentedAgent(
        pane_id=agent.pane_id,
        terminal_id=agent.terminal_id,
        workspace_id=agent.workspace_id,
        tab_id=agent.tab_id,
        state=agent.agent_status,
        revision=agent.revision,
    )


def build_herdr_reconcile_snapshot(
    *,
    herdr_alive: bool,
    snapshot: HerdrSessionSnapshot | None,
    reason: str | None = None,
) -> HerdrReconcileSnapshot:
    if not herdr_alive:
        return HerdrReconcileSnapshot(
            freshness="stale",
            reason=reason or "HERDR_NOT_RUNNING",
            agents=(),
        )
    if snapshot is None:
        return HerdrReconcileSnapshot(
            freshness="absent",
            reason=reason or "HERDR_SNAPSHOT_UNAVAILABLE",
            agents=(),
        )
    return HerdrReconcileSnapshot(
        freshness="fresh",
        reason=None,
        agents=tuple(presented_agent_from_session(item) for item in snapshot.agents),
        herdr_version=snapshot.version,
        herdr_protocol=snapshot.protocol,
    )


def find_linked_agent(
    metadata: TaskMetadataRecord,
    agents: tuple[HerdrPresentedAgent, ...],
) -> HerdrPresentedAgent | None:
    if not metadata.herdr_pane_id:
        return None
    for agent in agents:
        if (agent.pane_id == metadata.herdr_pane_id
            and (metadata.herdr_terminal_id is None or agent.terminal_id == metadata.herdr_terminal_id)
            and (metadata.herdr_workspace_id is None or agent.workspace_id == metadata.herdr_workspace_id)):
            return agent
    return None


def reconcile_task_view(
    metadata: TaskMetadataRecord,
    reconcile: HerdrReconcileSnapshot,
) -> ProjectedTaskView:
    agent = find_linked_agent(metadata, reconcile.agents)
    return project_task_view(
        metadata,
        herdr_agent=agent,
        freshness=reconcile.freshness,
    )


def projected_view_to_dict(view: ProjectedTaskView) -> dict[str, Any]:
    return {
        "schema_version": view.schema_version,
        "task_id": view.task_id,
        "correlation_id": view.correlation_id,
        "intent_label": view.intent_label,
        "runtime_authority": view.runtime_authority,
        "runtime_state": view.runtime_state,
        "freshness": view.freshness,
        "last_accepted_revision": view.last_accepted_revision,
        "herdr_pane_id": view.herdr_pane_id,
        "may_resume": view.may_resume,
        "is_terminal": view.is_terminal,
        "display_outcome": view.display_outcome,
        "reconciliation_required": view.reconciliation_required,
    }


def obtain_herdr_reconcile_snapshot(
    *,
    runtime_status: RuntimeStatus,
    snapshot_source: HerdrSnapshotSource | None,
) -> HerdrReconcileSnapshot:
    status = runtime_status()
    herdr_alive = bool(status.get("herdr_alive"))
    if not herdr_alive:
        return build_herdr_reconcile_snapshot(herdr_alive=False, snapshot=None)
    if snapshot_source is None:
        return build_herdr_reconcile_snapshot(
            herdr_alive=True,
            snapshot=None,
            reason="HERDR_SNAPSHOT_SOURCE_MISSING",
        )
    try:
        snapshot = snapshot_source.snapshot()
    except Exception as exc:
        return build_herdr_reconcile_snapshot(
            herdr_alive=False,
            snapshot=None,
            reason=type(exc).__name__,
        )
    return build_herdr_reconcile_snapshot(herdr_alive=True, snapshot=snapshot)


def build_reconcile_payload(
    product_root,
    *,
    task_id: str | None = None,
    runtime_status: RuntimeStatus | None = None,
    snapshot_source: HerdrSnapshotSource | None = None,
) -> dict[str, Any]:
    store = TaskMetadataStore(product_root)
    task_ids = (task_id,) if task_id else store.list_task_ids()
    status_fn = runtime_status or (lambda: RuntimeManager(product_root).status())
    reconcile = obtain_herdr_reconcile_snapshot(
        runtime_status=status_fn,
        snapshot_source=snapshot_source,
    )
    tasks: list[dict[str, Any]] = []
    for current_id in task_ids:
        metadata = store.load_optional(current_id)
        if metadata is None:
            continue
        agent = find_linked_agent(metadata, reconcile.agents)
        if (reconcile.freshness == 'fresh' and agent is not None
            and metadata.last_accepted_revision is not None
            and agent.revision > metadata.last_accepted_revision):
            metadata = store.save(replace(
                metadata, last_accepted_revision=agent.revision,
                updated_at=datetime.now(timezone.utc).isoformat(),
            ))
        view = reconcile_task_view(metadata, reconcile)
        tasks.append({
            **projected_view_to_dict(view),
            "metadata": {
                "recorded_at": metadata.recorded_at,
                "updated_at": metadata.updated_at,
                "approval_refs": list(metadata.approval_refs),
                "artifact_refs": list(metadata.artifact_refs),
            },
        })
    return {
        "schema_version": 1,
        "runtime_authority": RUNTIME_AUTHORITY,
        "freshness": reconcile.freshness,
        "reason": reconcile.reason,
        "herdr_version": reconcile.herdr_version,
        "herdr_protocol": reconcile.herdr_protocol,
        "tasks": tasks,
    }
