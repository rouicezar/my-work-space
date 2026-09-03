"""Candidate and approval policy bound to Semantica as confirmed authority."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

CONFIRMED_AUTHORITY = "semantica"
CONFIRMED_METADATA_STATUS = "confirmed"
CANDIDATE_PENDING_STATUS = "pending"
CANDIDATE_TERMINAL_STATUSES = frozenset({"confirmed", "rejected", "duplicate", "conflict"})
CORRELATION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class MemoryGovernanceError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SourceReference:
    uri: str
    observed_at: str
    digest: str | None = None


def build_confirmed_metadata(
    *,
    record_id: str,
    claim_key: str,
    version: int,
    previous_record_id: str | None,
    sources: list[SourceReference] | tuple[SourceReference, ...],
    correlation_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "record_id": record_id,
        "claim_key": claim_key,
        "status": CONFIRMED_METADATA_STATUS,
        "version": version,
        "previous_record_id": previous_record_id,
        "sources": [asdict(source) for source in sources],
        "correlation_id": correlation_id,
    }


def validate_confirmed_metadata(metadata: dict[str, Any]) -> None:
    if metadata.get("schema_version") != 1:
        raise MemoryGovernanceError("MEMORY_METADATA_INVALID", "schema_version")
    if metadata.get("status") != CONFIRMED_METADATA_STATUS:
        raise MemoryGovernanceError("MEMORY_METADATA_INVALID", "status")
    record_id = metadata.get("record_id")
    claim_key = metadata.get("claim_key")
    version = metadata.get("version")
    if not isinstance(record_id, str) or not record_id.strip():
        raise MemoryGovernanceError("MEMORY_METADATA_INVALID", "record_id")
    if not isinstance(claim_key, str) or not claim_key.strip():
        raise MemoryGovernanceError("MEMORY_METADATA_INVALID", "claim_key")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise MemoryGovernanceError("MEMORY_METADATA_INVALID", "version")


class UnavailableSemanticaBackend:
    """Fail-closed Semantica stand-in when embedding/runtime is not verified."""

    def health(self) -> dict[str, str]:
        return {"status": "unavailable", "code": "EMBEDDING_ROUTE_UNVERIFIED"}

    def store(self, content: str, metadata: dict[str, Any]) -> str:
        raise MemoryGovernanceError("SEMANTICA_UNAVAILABLE", "confirmed memory authority is unavailable")

    def get(self, memory_id: str) -> None:
        return None

    def retrieve(self, query: str, limit: int) -> list[dict[str, Any]]:
        return []

    def forget(self, memory_id: str) -> bool:
        return False
