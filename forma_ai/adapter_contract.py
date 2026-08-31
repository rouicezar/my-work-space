"""Stable vendor-neutral envelopes shared by Forma AI adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AdapterIdentity:
    adapter_id: str
    adapter_version: str
    protocol_version: str
    upstream_id: str
    upstream_version: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityDeclaration:
    capability_id: str
    operations: tuple[str, ...]
    proof: str

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "operations": list(self.operations),
            "proof": self.proof,
        }


@dataclass(frozen=True)
class PolicyPreview:
    correlation_id: str
    action: str
    data_classes: tuple[str, ...]
    external_write: bool
    approval_required: bool
    payload_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "correlation_id": self.correlation_id,
            "action": self.action,
            "data_classes": list(self.data_classes),
            "external_write": self.external_write,
            "approval_required": self.approval_required,
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True)
class AuditEnvelope:
    event_id: str
    correlation_id: str
    action: str
    outcome: str
    occurred_at: str
    redacted_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "action": self.action,
            "outcome": self.outcome,
            "occurred_at": self.occurred_at,
            "redacted_fields": list(self.redacted_fields),
        }


@dataclass(frozen=True)
class HealthEnvelope:
    schema_version: int
    status: str
    reachable: bool
    ready: bool
    proof: str
    checked_at: str
    reason_code: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
