"""Offline local-first eligibility and exact cloud escalation proposals."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

from mac_ai_work_os.cloud_catalog import CloudProvider


BLOCKED_DATA_CLASSES = frozenset({
    "credentials", "authentication_material", "regulated_secrets",
    "third_party_sensitive_personal_data",
})
DATA_CLASSES = BLOCKED_DATA_CLASSES | frozenset({
    "user_text", "document_content", "confirmed_memory", "tool_result",
})
REASONS = frozenset({
    "local_unhealthy", "local_profile_unverified", "context_exceeds_local_limit",
    "required_capability_missing", "local_resource_insufficient", "local_validation_failed",
})
CORRELATION = re.compile(r"^[0-9a-f-]{36}$")


class RoutingError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class TaskRequirements:
    estimated_input_tokens: int
    maximum_output_tokens: int
    required_capabilities: frozenset[str]
    minimum_available_memory_mb: int
    data_classes: frozenset[str]


@dataclass(frozen=True)
class LocalProfile:
    verified: bool
    healthy: bool
    context_window_tokens: int
    capabilities: frozenset[str]
    available_memory_mb: int


@dataclass(frozen=True)
class RouteDecision:
    route: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CostEstimate:
    currency: str
    minimum: float
    maximum: float
    pricing_source: str
    pricing_effective_at: str


@dataclass(frozen=True)
class CloudEscalationProposal:
    schema_version: int
    proposal_id: str
    correlation_id: str
    provider_id: str
    model_id: str
    reason_codes: tuple[str, ...]
    payload_sha256: str
    payload_size_bytes: int
    data_classes: tuple[str, ...]
    redactions: tuple[str, ...]
    maximum_output_tokens: int
    estimated_cost: CostEstimate
    processing_location: str
    retention: str
    training_opt_out_state: str
    privacy_policy_url: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def decide_route(requirements: TaskRequirements, profile: LocalProfile) -> RouteDecision:
    _validate_requirements(requirements)
    reasons: list[str] = []
    if not profile.verified:
        reasons.append("local_profile_unverified")
    if not profile.healthy:
        reasons.append("local_unhealthy")
    if requirements.estimated_input_tokens + requirements.maximum_output_tokens > profile.context_window_tokens:
        reasons.append("context_exceeds_local_limit")
    if not requirements.required_capabilities.issubset(profile.capabilities):
        reasons.append("required_capability_missing")
    if profile.available_memory_mb < requirements.minimum_available_memory_mb:
        reasons.append("local_resource_insufficient")
    return RouteDecision("local" if not reasons else "cloud_proposal_required", tuple(reasons))


def create_cloud_proposal(
    *, correlation_id: str, provider: CloudProvider, model_id: str,
    requirements: TaskRequirements, reason_codes: tuple[str, ...],
    outbound_body: dict[str, object], redactions: tuple[str, ...], now: datetime,
) -> tuple[CloudEscalationProposal, bytes]:
    _validate_requirements(requirements)
    try:
        parsed = uuid.UUID(correlation_id)
    except ValueError as exc:
        raise RoutingError("CORRELATION_INVALID", correlation_id) from exc
    if str(parsed) != correlation_id.lower() or not CORRELATION.fullmatch(correlation_id):
        raise RoutingError("CORRELATION_INVALID", correlation_id)
    if not reason_codes or any(code not in REASONS for code in reason_codes):
        raise RoutingError("ESCALATION_REASON_INVALID", str(reason_codes))
    blocked = requirements.data_classes & BLOCKED_DATA_CLASSES
    if blocked:
        raise RoutingError("CLOUD_DATA_CLASS_BLOCKED", ",".join(sorted(blocked)))
    model = provider.model(model_id)
    if not requirements.required_capabilities.issubset(model.capabilities):
        raise RoutingError("CLOUD_CAPABILITY_MISSING", model_id)
    if requirements.estimated_input_tokens + requirements.maximum_output_tokens > model.context_window_tokens:
        raise RoutingError("CLOUD_CONTEXT_EXCEEDED", model_id)
    if requirements.maximum_output_tokens > model.maximum_output_tokens:
        raise RoutingError("CLOUD_OUTPUT_LIMIT_EXCEEDED", model_id)
    if not provider.pricing_is_current(now):
        raise RoutingError("CLOUD_PRICING_STALE", provider.pricing_source)
    body = _canonical_json(outbound_body)
    prices = model.prices
    input_millions = requirements.estimated_input_tokens / 1_000_000
    output_millions = requirements.maximum_output_tokens / 1_000_000
    minimum = input_millions * prices.cache_miss_off_peak + output_millions * prices.output_off_peak
    maximum = input_millions * prices.cache_miss_peak + output_millions * prices.output_peak
    proposal = CloudEscalationProposal(
        schema_version=1, proposal_id=str(uuid.uuid4()), correlation_id=correlation_id,
        provider_id=provider.id, model_id=model.id, reason_codes=reason_codes,
        payload_sha256=hashlib.sha256(body).hexdigest(), payload_size_bytes=len(body),
        data_classes=tuple(sorted(requirements.data_classes)), redactions=redactions,
        maximum_output_tokens=requirements.maximum_output_tokens,
        estimated_cost=CostEstimate(
            "USD", round(minimum, 8), round(maximum, 8), provider.pricing_source,
            provider.pricing_effective_at.isoformat(),
        ),
        processing_location=provider.processing_location, retention=provider.retention,
        training_opt_out_state=provider.training_opt_out_state,
        privacy_policy_url=provider.privacy_policy_url,
    )
    return proposal, body


def _validate_requirements(requirements: TaskRequirements) -> None:
    numbers = (
        requirements.estimated_input_tokens, requirements.maximum_output_tokens,
        requirements.minimum_available_memory_mb,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in numbers):
        raise RoutingError("TASK_REQUIREMENTS_INVALID", str(numbers))
    if not requirements.required_capabilities or not requirements.data_classes:
        raise RoutingError("TASK_REQUIREMENTS_INVALID", "capabilities and data classes are required")
    if not requirements.data_classes.issubset(DATA_CLASSES):
        raise RoutingError("TASK_DATA_CLASS_INVALID", str(requirements.data_classes))


def _canonical_json(body: dict[str, object]) -> bytes:
    try:
        encoded = json.dumps(
            body, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RoutingError("CLOUD_PAYLOAD_INVALID", "payload must be finite JSON") from exc
    if len(encoded) > 8 * 1024 * 1024:
        raise RoutingError("CLOUD_PAYLOAD_TOO_LARGE", str(len(encoded)))
    return encoded
