"""Deterministic local-first planning for one user-visible task submission."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

from mac_ai_work_os.cloud_preferences import CloudPreferenceState
from mac_ai_work_os.inference_routing import (
    LocalProfile, RouteDecision, TaskRequirements, decide_route,
)
from mac_ai_work_os.local_profiles import VerifiedLocalProfile
from mac_ai_work_os.local_tasks import LocalTaskError, LocalTaskRequest, parse_local_task


MAXIMUM_UNIFIED_TASK_BYTES = 1024 * 1024


class TaskOrchestratorError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class UnifiedTaskRequest:
    schema_version: int
    prompt: str
    maximum_output_tokens: int
    required_capabilities: frozenset[str]
    data_classes: frozenset[str]


@dataclass(frozen=True)
class UnifiedTaskPlan:
    schema_version: int
    route: str
    reason_codes: tuple[str, ...]
    estimated_input_tokens: int
    maximum_output_tokens: int
    local_profile_id: str
    local_evidence_status: str
    cloud_enabled: bool
    cloud_state_code: str


def parse_unified_task(data: bytes) -> UnifiedTaskRequest:
    if not data or len(data) > MAXIMUM_UNIFIED_TASK_BYTES:
        raise TaskOrchestratorError("TASK_SIZE_INVALID", str(len(data)))
    try:
        raw = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TaskOrchestratorError("TASK_JSON_INVALID", "task must be UTF-8 JSON") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "prompt", "maximum_output_tokens",
        "required_capabilities", "data_classes",
    }:
        raise TaskOrchestratorError("TASK_SCHEMA_INVALID", "unexpected task fields")
    try:
        local = parse_local_task(json.dumps({
            "schema_version": raw["schema_version"], "prompt": raw["prompt"],
            "maximum_output_tokens": raw["maximum_output_tokens"],
        }, ensure_ascii=False).encode("utf-8"))
    except LocalTaskError as exc:
        raise TaskOrchestratorError(exc.code, str(exc)) from exc
    capabilities = raw["required_capabilities"]
    classes = raw["data_classes"]
    if (
        not isinstance(capabilities, list) or not capabilities
        or any(not isinstance(item, str) for item in capabilities)
        or len(capabilities) != len(set(capabilities))
        or not isinstance(classes, list) or not classes
        or any(not isinstance(item, str) for item in classes)
        or len(classes) != len(set(classes))
    ):
        raise TaskOrchestratorError("TASK_REQUIREMENTS_INVALID", "task requirement arrays")
    return UnifiedTaskRequest(
        1, local.prompt, local.maximum_output_tokens,
        frozenset(capabilities), frozenset(classes),
    )


def estimate_input_tokens(prompt: str) -> int:
    # Conservative without loading model tokenizer: at least one token per two UTF-8 bytes.
    return max(1, math.ceil(len(prompt.encode("utf-8")) / 2))


def plan_unified_task(
    task: UnifiedTaskRequest, *, profile: VerifiedLocalProfile,
    runtime_healthy: bool, available_memory_mb: int,
    cloud: CloudPreferenceState,
) -> tuple[UnifiedTaskPlan, TaskRequirements, RouteDecision]:
    requirements = TaskRequirements(
        estimated_input_tokens=estimate_input_tokens(task.prompt),
        maximum_output_tokens=task.maximum_output_tokens,
        required_capabilities=task.required_capabilities,
        minimum_available_memory_mb=profile.minimum_available_memory_mb,
        data_classes=task.data_classes,
    )
    local = LocalProfile(
        verified=profile.evidence_status.startswith("verified_"),
        healthy=runtime_healthy,
        context_window_tokens=profile.context_window_tokens,
        capabilities=profile.capabilities,
        available_memory_mb=available_memory_mb,
    )
    decision = decide_route(requirements, local)
    if decision.route == "local" and task.maximum_output_tokens > profile.maximum_output_tokens:
        decision = RouteDecision("cloud_proposal_required", ("local_output_limit_exceeded",))
    if decision.route == "local":
        route = "local"
    elif cloud.valid and cloud.enabled:
        route = "cloud_proposal_required"
    else:
        route = "capability_unavailable"
    plan = UnifiedTaskPlan(
        1, route, decision.reasons, requirements.estimated_input_tokens,
        task.maximum_output_tokens, profile.id, profile.evidence_status,
        cloud.enabled if cloud.valid else False, cloud.code,
    )
    return plan, requirements, decision


def local_task_from_unified(task: UnifiedTaskRequest) -> LocalTaskRequest:
    return LocalTaskRequest(1, task.prompt, task.maximum_output_tokens)
