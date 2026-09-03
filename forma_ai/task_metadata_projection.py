"""Product task metadata projection bounded by Herdr runtime authority.

The product may persist intent, correlation, approval, and artifact metadata.
Runtime completion, resumability, and semantic agent state always come from a
fresh Herdr snapshot/event reconcile — never from metadata alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from forma_ai.herdr_adapter import HerdrAdapter
from forma_ai.herdr_presentation import HerdrPresentedAgent


RUNTIME_AUTHORITY = "herdr"
PROJECTION_SCHEMA_VERSION = 1

PRODUCT_OWNED_FIELDS = (
    "task_id",
    "correlation_id",
    "run_id",
    "intent_label",
    "herdr_pane_id",
    "herdr_workspace_id",
    "herdr_tab_id",
    "herdr_terminal_id",
    "last_accepted_revision",
    "approval_refs",
    "artifact_refs",
    "policy_preview_digest",
    "recorded_at",
    "updated_at",
)

FORBIDDEN_METADATA_CLAIMS = frozenset({
    "completed",
    "succeeded",
    "failed",
    "cancelled",
    "resumable",
    "runtime_state",
    "runtime_phase",
    "agent_status",
    "may_resume",
    "is_terminal",
    "display_outcome",
})

TERMINAL_RUNTIME_STATES = frozenset({
    "succeeded",
    "failed",
    "cancelled",
})

RESUMABLE_RUNTIME_STATES = frozenset({
    "interrupted",
    "blocked",
    "failed",
    "unknown",
})


class TaskMetadataProjectionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class TaskMetadataRecord:
    task_id: str
    correlation_id: str
    intent_label: str
    recorded_at: str
    updated_at: str
    run_id: str | None = None
    herdr_pane_id: str | None = None
    herdr_workspace_id: str | None = None
    herdr_tab_id: str | None = None
    herdr_terminal_id: str | None = None
    last_accepted_revision: int | None = None
    approval_refs: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    policy_preview_digest: str | None = None


@dataclass(frozen=True)
class ProjectedTaskView:
    schema_version: int
    task_id: str
    correlation_id: str
    intent_label: str
    runtime_authority: str
    runtime_state: str
    freshness: str
    last_accepted_revision: int | None
    herdr_pane_id: str | None
    may_resume: bool
    is_terminal: bool
    display_outcome: str
    reconciliation_required: bool


def normalize_runtime_state(raw_agent_status: str) -> str:
    """Map Herdr pane agent_status values to adapter contract runtime states."""
    return HerdrAdapter._task_state(raw_agent_status)


def binding_contract() -> dict[str, Any]:
    return {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "runtime_authority": RUNTIME_AUTHORITY,
        "product_owned_fields": list(PRODUCT_OWNED_FIELDS),
        "forbidden_metadata_claims": sorted(FORBIDDEN_METADATA_CLAIMS),
        "terminal_runtime_states": sorted(TERMINAL_RUNTIME_STATES),
        "resumable_runtime_states": sorted(RESUMABLE_RUNTIME_STATES),
    }


def validate_metadata_payload(payload: Mapping[str, Any]) -> None:
    forbidden = FORBIDDEN_METADATA_CLAIMS.intersection(payload.keys())
    if forbidden:
        raise TaskMetadataProjectionError(
            "METADATA_CLAIMS_RUNTIME_AUTHORITY",
            f"metadata must not claim runtime fields: {sorted(forbidden)}",
        )


def validate_metadata_record(record: TaskMetadataRecord) -> None:
    if not record.task_id or not record.correlation_id:
        raise TaskMetadataProjectionError("METADATA_INVALID", "task_id and correlation_id are required")
    if not record.intent_label.strip():
        raise TaskMetadataProjectionError("METADATA_INVALID", "intent_label is required")
    if record.last_accepted_revision is not None and record.last_accepted_revision < 0:
        raise TaskMetadataProjectionError("METADATA_INVALID", "last_accepted_revision must be nonnegative")


def project_task_view(
    metadata: TaskMetadataRecord,
    *,
    herdr_agent: HerdrPresentedAgent | None,
    freshness: str,
) -> ProjectedTaskView:
    validate_metadata_record(metadata)
    normalized_freshness = freshness if freshness in {"fresh", "stale", "absent"} else "absent"
    runtime_state = "unknown"
    reconciliation_required = normalized_freshness != "fresh" or herdr_agent is None
    revision_matches = (
        herdr_agent is not None
        and metadata.last_accepted_revision is not None
        and herdr_agent.revision >= metadata.last_accepted_revision
        and metadata.herdr_pane_id == herdr_agent.pane_id
    )

    if herdr_agent is not None and normalized_freshness == "fresh":
        runtime_state = normalize_runtime_state(herdr_agent.state)
        if metadata.herdr_pane_id and metadata.herdr_pane_id != herdr_agent.pane_id:
            reconciliation_required = True
            runtime_state = "unknown"
        elif metadata.last_accepted_revision is not None and herdr_agent.revision < metadata.last_accepted_revision:
            reconciliation_required = True
            runtime_state = "unknown"

    may_resume = (
        normalized_freshness == "fresh"
        and herdr_agent is not None
        and revision_matches
        and runtime_state in RESUMABLE_RUNTIME_STATES
    )
    is_terminal = (
        normalized_freshness == "fresh"
        and herdr_agent is not None
        and revision_matches
        and runtime_state in TERMINAL_RUNTIME_STATES
    )

    if reconciliation_required or runtime_state == "unknown":
        display_outcome = "unknown"
    elif is_terminal:
        display_outcome = runtime_state
    elif runtime_state in {"running", "starting", "queued"}:
        display_outcome = "in_progress"
    elif may_resume:
        display_outcome = "recoverable"
    else:
        display_outcome = "unknown"

    if display_outcome in {"succeeded", "completed"} and not is_terminal:
        raise TaskMetadataProjectionError(
            "PROJECTION_RUNTIME_CLAIM_DENIED",
            "metadata projection cannot declare completion without fresh Herdr proof",
        )
    if may_resume and not (
        normalized_freshness == "fresh"
        and herdr_agent is not None
        and revision_matches
        and runtime_state in RESUMABLE_RUNTIME_STATES
    ):
        raise TaskMetadataProjectionError(
            "PROJECTION_RESUME_CLAIM_DENIED",
            "metadata projection cannot declare resumability without fresh Herdr proof",
        )

    return ProjectedTaskView(
        schema_version=PROJECTION_SCHEMA_VERSION,
        task_id=metadata.task_id,
        correlation_id=metadata.correlation_id,
        intent_label=metadata.intent_label,
        runtime_authority=RUNTIME_AUTHORITY,
        runtime_state=runtime_state,
        freshness=normalized_freshness,
        last_accepted_revision=metadata.last_accepted_revision,
        herdr_pane_id=metadata.herdr_pane_id,
        may_resume=may_resume,
        is_terminal=is_terminal,
        display_outcome=display_outcome,
        reconciliation_required=reconciliation_required,
    )
