"""Prove task rediscovery after app reopen and Herdr detach/reconnect."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from forma_ai.herdr_adapter import HerdrAdapter, HerdrSessionAgent, HerdrSessionSnapshot
from forma_ai.task_history_recovery import RecoveryContext, execute_reclaim
from forma_ai.task_metadata_projection import TaskMetadataRecord
from forma_ai.task_metadata_reconcile import (
    find_linked_agent,
    obtain_herdr_reconcile_snapshot,
    reconcile_task_view,
    build_reconcile_payload,
)
from forma_ai.task_metadata_store import TaskMetadataStore


RuntimeStatus = Callable[[], dict[str, object]]


class TaskHistoryRediscoveryError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RediscoveryObservation:
    phase: str
    task_count: int
    tasks: tuple[dict[str, Any], ...]


def binding_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "proof_phases": ["app_reopened", "herdr_detached", "herdr_reconnected"],
        "runtime_authority": "herdr",
        "false_completion_forbidden": True,
    }


def list_rediscovered_task_ids(product_root) -> tuple[str, ...]:
    return TaskMetadataStore(product_root).list_task_ids()


def observe_rediscovery(
    product_root,
    *,
    phase: str,
    runtime_status: RuntimeStatus,
    snapshot_source,
) -> RediscoveryObservation:
    payload = build_reconcile_payload(
        product_root,
        runtime_status=runtime_status,
        snapshot_source=snapshot_source,
    )
    tasks = tuple(payload.get("tasks", ()))
    return RediscoveryObservation(phase=phase, task_count=len(tasks), tasks=tasks)


def evaluate_rediscovery_proof(payload: dict[str, Any]) -> dict[str, Any]:
    required = (
        "rediscovered_task_ids",
        "detached_all_unknown",
        "reconnected_without_false_completion",
        "recoverable_after_reconnect",
        "reclaim_after_reopen",
    )
    missing = [field for field in required if field not in payload]
    if missing:
        return {"status": "proof_failed", "reason": "payload_incomplete", "missing": missing}
    if not payload.get("rediscovered_task_ids"):
        return {"status": "proof_failed", "reason": "tasks_not_rediscovered"}
    if not payload.get("detached_all_unknown"):
        return {"status": "proof_failed", "reason": "detach_did_not_fail_closed"}
    if not payload.get("reconnected_without_false_completion"):
        return {"status": "proof_failed", "reason": "false_completion_detected"}
    if not payload.get("recoverable_after_reconnect"):
        return {"status": "proof_failed", "reason": "recovery_state_missing"}
    if not payload.get("reclaim_after_reopen"):
        return {"status": "proof_failed", "reason": "reclaim_after_reopen_failed"}
    return {"status": "proof_passed", "reason": None, **{key: payload[key] for key in required}}


def run_rediscovery_proof(
    product_root,
    *,
    records: tuple[TaskMetadataRecord, ...],
    detached_status: RuntimeStatus,
    reconnected_status: RuntimeStatus,
    reconnected_snapshot_source,
    reclaim_adapter: HerdrAdapter,
) -> dict[str, Any]:
    store = TaskMetadataStore(product_root)
    if not records:
        raise TaskHistoryRediscoveryError("REDISCOVERY_EMPTY", "no persisted tasks to rediscover")
    for record in records:
        store.save(record)

    reopened_ids = list_rediscovered_task_ids(product_root)
    if len(reopened_ids) != len(records):
        raise TaskHistoryRediscoveryError(
            "REDISCOVERY_COUNT_MISMATCH",
            "persisted tasks were not fully rediscovered after reopen",
        )

    detached = observe_rediscovery(
        product_root,
        phase="herdr_detached",
        runtime_status=detached_status,
        snapshot_source=None,
    )
    detached_all_unknown = bool(detached.tasks) and all(
        task.get("runtime_state") == "unknown"
        and task.get("display_outcome") == "unknown"
        and not task.get("is_terminal")
        for task in detached.tasks
    )

    reconnected = observe_rediscovery(
        product_root,
        phase="herdr_reconnected",
        runtime_status=reconnected_status,
        snapshot_source=reconnected_snapshot_source,
    )
    if reconnected.task_count != len(records):
        raise TaskHistoryRediscoveryError(
            "REDISCOVERY_COUNT_MISMATCH",
            "reconnected reconcile lost persisted tasks",
        )

    false_completion = any(
        task.get("is_terminal")
        and task.get("freshness") != "fresh"
        for task in reconnected.tasks
    )
    recoverable = any(task.get("may_resume") for task in reconnected.tasks)
    terminal_with_fresh_proof = any(
        task.get("is_terminal")
        and task.get("freshness") == "fresh"
        and task.get("display_outcome") == "succeeded"
        for task in reconnected.tasks
    )

    reclaim_after_reopen = False
    reconcile = obtain_herdr_reconcile_snapshot(
        runtime_status=reconnected_status,
        snapshot_source=reconnected_snapshot_source,
    )
    for task in reconnected.tasks:
        if not task.get("may_resume"):
            continue
        metadata = store.load(task["task_id"])
        agent = find_linked_agent(metadata, reconcile.agents)
        if agent is None:
            continue
        context = RecoveryContext(
            metadata=metadata,
            view=reconcile_task_view(metadata, reconcile),
            agent=agent,
        )
        execute_reclaim(context, reclaim_adapter)
        reclaim_after_reopen = True
        break

    payload = {
        "schema_version": 1,
        "rediscovered_task_ids": list(reopened_ids),
        "detached_all_unknown": detached_all_unknown,
        "reconnected_without_false_completion": not false_completion,
        "recoverable_after_reconnect": recoverable,
        "reclaim_after_reopen": reclaim_after_reopen,
        "terminal_with_fresh_herdr_proof": terminal_with_fresh_proof,
        "phases": {
            "app_reopened": {"task_ids": list(reopened_ids)},
            "herdr_detached": {
                "freshness": detached.tasks[0].get("freshness") if detached.tasks else None,
            },
            "herdr_reconnected": {
                "freshness": reconnected.tasks[0].get("freshness") if reconnected.tasks else None,
            },
        },
    }
    result = evaluate_rediscovery_proof(payload)
    return {**payload, **result}


def multi_agent_snapshot(*agents: dict[str, Any]) -> HerdrSessionSnapshot:
    return HerdrSessionSnapshot(
        version="0.8.2",
        protocol=20,
        workspaces=(),
        tabs=(),
        panes=(),
        agents=tuple(HerdrSessionAgent(**item) for item in agents),
        layouts=(),
    )
