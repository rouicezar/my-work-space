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
