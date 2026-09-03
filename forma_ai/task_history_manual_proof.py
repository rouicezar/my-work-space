"""Interrupted-task manual recovery proof recorder and validator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.task_history_binding import TASK_HISTORY_RECOVERY_AUDIT_PATH, SUPERVISOR_COMMANDS
from forma_ai.task_history_rediscovery import (
    list_rediscovered_task_ids,
    observe_rediscovery,
    run_rediscovery_proof,
)
from forma_ai.task_metadata_projection import TaskMetadataRecord


@dataclass(frozen=True)
class ManualRecoveryScenario:
    scenario_id: str
    title: str
    description: str


INTERRUPTED_TASK_SCENARIO = ManualRecoveryScenario(
    scenario_id="interrupted_blocked_task",
    title="Interrupted blocked task recovery",
    description=(
        "A task was interrupted while Herdr reported blocked state. "
        "After app reopen and Herdr detach/reconnect, the operator must see "
        "recoverable state and may reclaim only with fresh Herdr proof."
    ),
)


MANUAL_CHECKLIST = (
    "native_history_lists_persisted_task_after_reopen",
    "history_shows_unknown_while_herdr_detached",
    "reclaim_enabled_only_with_fresh_herdr",
    "recovery_audit_log_written",
    "no_false_completion_without_herdr",
)


def binding_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "scenario_id": INTERRUPTED_TASK_SCENARIO.scenario_id,
        "supervisor_commands": dict(SUPERVISOR_COMMANDS),
        "recovery_audit_path": TASK_HISTORY_RECOVERY_AUDIT_PATH,
        "manual_checklist": list(MANUAL_CHECKLIST),
    }


def interrupted_task_record(**overrides) -> TaskMetadataRecord:
    base = {
        "task_id": "task-interrupted-1",
        "correlation_id": "corr-interrupted-1",
        "intent_label": "Interrupted research synthesis",
        "recorded_at": "2026-09-04T00:00:00+00:00",
        "updated_at": "2026-09-04T00:00:00+00:00",
        "run_id": "run-interrupted-1",
        "herdr_pane_id": "pane-interrupted-1",
        "herdr_workspace_id": "workspace-1",
        "herdr_tab_id": "tab-1",
        "herdr_terminal_id": "terminal-interrupted-1",
        "last_accepted_revision": 6,
        "approval_refs": ("approval:cloud:proof",),
        "artifact_refs": ("artifact:draft:notes",),
    }
    base.update(overrides)
    return TaskMetadataRecord(**base)


def run_automated_recovery_proof(
    product_root,
    *,
    detached_status: Callable[[], dict[str, object]],
    reconnected_status: Callable[[], dict[str, object]],
    reconnected_snapshot_source,
    reclaim_adapter: HerdrAdapter,
) -> dict[str, Any]:
    record = interrupted_task_record()
    proof = run_rediscovery_proof(
        product_root,
        records=(record,),
        detached_status=detached_status,
        reconnected_status=reconnected_status,
        reconnected_snapshot_source=reconnected_snapshot_source,
        reclaim_adapter=reclaim_adapter,
    )
    reopened = list_rediscovered_task_ids(product_root)
    detached = observe_rediscovery(
        product_root,
        phase="herdr_detached",
        runtime_status=detached_status,
        snapshot_source=None,
    )
    reconnected = observe_rediscovery(
        product_root,
        phase="herdr_reconnected",
        runtime_status=reconnected_status,
        snapshot_source=reconnected_snapshot_source,
    )
    interrupted_task = next(
        (task for task in reconnected.tasks if task["task_id"] == record.task_id),
        None,
    )
    reclaim_verified = proof.get("reclaim_after_reopen", False)
    return {
        "status": "automated_proof_passed" if proof.get("status") == "proof_passed" else "automated_proof_failed",
        "scenario_id": INTERRUPTED_TASK_SCENARIO.scenario_id,
        "rediscovered_task_ids": list(reopened),
        "detached_unknown": detached.tasks[0]["runtime_state"] == "unknown" if detached.tasks else False,
        "reconnected_may_resume": bool(interrupted_task and interrupted_task.get("may_resume")),
        "reclaim_after_reopen": reclaim_verified,
        "proof": proof,
    }


def evaluate_recovery_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    automated = payload.get("automated", {})
    required = (
        "rediscovered_task_ids",
        "detached_unknown",
        "reconnected_may_resume",
        "reclaim_after_reopen",
    )
    missing = [field for field in required if field not in automated]
    if missing:
        return {"status": "proof_failed", "reason": "automated_incomplete", "missing": missing}
    if automated.get("status") != "automated_proof_passed":
        return {"status": "proof_failed", "reason": "automated_proof_failed"}
    if not automated.get("rediscovered_task_ids"):
        return {"status": "proof_failed", "reason": "tasks_not_rediscovered"}
    if not automated.get("detached_unknown"):
        return {"status": "proof_failed", "reason": "detach_not_unknown"}
    if not automated.get("reconnected_may_resume"):
        return {"status": "proof_failed", "reason": "not_recoverable_after_reconnect"}
    if not automated.get("reclaim_after_reopen"):
        return {"status": "proof_failed", "reason": "reclaim_not_verified"}
    manual = payload.get("manual_checklist", {})
    return {
        "status": "proof_recorded",
        "reason": None,
        "automated_verified": True,
        "manual_signoff_required": any(not manual.get(item) for item in MANUAL_CHECKLIST),
        "manual_checklist": manual,
    }


def render_recovery_evidence_markdown(
    payload: dict[str, Any],
    *,
    proof_date: str | None = None,
) -> str:
    when = proof_date or date.today().isoformat()
    automated = payload.get("automated", {})
    manual = payload.get("manual_checklist", {})
    evaluation = payload.get("evaluation", {})
    lines = [
        f"# Recovery Proof — {when}",
        "",
        f"Task: P8-T06",
        f"Scenario: {INTERRUPTED_TASK_SCENARIO.title}",
        f"Status: {evaluation.get('status', 'draft')}",
        "",
        "## Scenario",
        "",
        INTERRUPTED_TASK_SCENARIO.description,
        "",
        "## Automated verification (machine)",
        "",
        f"- rediscovered_task_ids: `{automated.get('rediscovered_task_ids', [])}`",
        f"- detached_unknown: `{automated.get('detached_unknown')}`",
        f"- reconnected_may_resume: `{automated.get('reconnected_may_resume')}`",
        f"- reclaim_after_reopen: `{automated.get('reclaim_after_reopen')}`",
        f"- automated_status: `{automated.get('status')}`",
        "",
        "## Manual verification (operator — native History UI)",
        "",
    ]
    for item in MANUAL_CHECKLIST:
        checked = "x" if manual.get(item) else " "
        lines.append(f"- [{checked}] `{item}`")
    lines.extend([
        "",
        "## Manual sign-off",
        "",
        f"- operator: `{payload.get('operator', 'pending')}`",
        f"- signoff_at: `{payload.get('signoff_at', 'pending')}`",
        f"- notes: {payload.get('notes', 'Complete the checklist above in the native workbench with Herdr/runtime online.')}",
        "",
        "## Commands referenced",
        "",
        f"- reconcile: `{SUPERVISOR_COMMANDS['reconcile']}`",
        f"- reclaim: `{SUPERVISOR_COMMANDS['reclaim']}`",
        f"- audit: `{TASK_HISTORY_RECOVERY_AUDIT_PATH}`",
        "",
    ])
    return "\n".join(lines)


def build_recovery_evidence_payload(
    product_root,
    *,
    detached_status: Callable[[], dict[str, object]],
    reconnected_status: Callable[[], dict[str, object]],
    reconnected_snapshot_source,
    reclaim_adapter: HerdrAdapter,
    manual_checklist: dict[str, bool] | None = None,
) -> dict[str, Any]:
    automated = run_automated_recovery_proof(
        product_root,
        detached_status=detached_status,
        reconnected_status=reconnected_status,
        reconnected_snapshot_source=reconnected_snapshot_source,
        reclaim_adapter=reclaim_adapter,
    )
    payload = {
        "schema_version": 1,
        "scenario_id": INTERRUPTED_TASK_SCENARIO.scenario_id,
        "automated": automated,
        "manual_checklist": manual_checklist or {item: False for item in MANUAL_CHECKLIST},
        "operator": "pending",
        "signoff_at": "pending",
    }
    payload["evaluation"] = evaluate_recovery_evidence(payload)
    return payload
