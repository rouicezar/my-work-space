"""Product governance boundary for confirmed Semantica knowledge.

The local SQLite ``records`` table is a **workflow projection**, not a competing
authority. Confirmed reads and exports must use Semantica content via
``SemanticaBackend.get()`` after metadata binding checks. Denormalized ``content``
columns exist for offline review/history only and may lag upstream until corrected
through the governed ``correct()`` path.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from forma_ai.memory_governance_policy import (
    CONFIRMED_AUTHORITY,
    CORRELATION,
    MemoryGovernanceError,
    SourceReference,
    build_confirmed_metadata,
    validate_confirmed_metadata,
)

__all__ = [
    "CORRELATION",
    "Candidate",
    "ConfirmedMemory",
    "GovernedMemory",
    "MemoryGovernanceError",
    "SemanticaBackend",
    "SourceReference",
]


class SemanticaBackend(Protocol):
    def store(self, content: str, metadata: dict[str, Any]) -> str: ...
    def get(self, memory_id: str) -> dict[str, Any] | None: ...
    def retrieve(self, query: str, limit: int) -> list[dict[str, Any]]: ...
    def forget(self, memory_id: str) -> bool: ...
    def health(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    claim_key: str
    content: str
    sources: tuple[SourceReference, ...]
    correlation_id: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ConfirmedMemory:
    record_id: str
    semantica_id: str
    claim_key: str
    content: str
    sources: tuple[SourceReference, ...]
    correlation_id: str
    version: int
    previous_record_id: str | None
    created_at: str
    updated_at: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GovernedMemory:
    """Keep candidates separate and expose only Semantica-confirmed records."""

    def __init__(self, root: Path, backend: SemanticaBackend):
        if not root.is_absolute():
            raise MemoryGovernanceError("MEMORY_ROOT_INVALID", "memory root must be absolute")
        self.root = root
        self.backend = backend
        self.database = root / "state/memory/governance.sqlite3"
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        os.chmod(self.database, 0o600)

    def propose(
        self,
        *,
        claim_key: str,
        content: str,
        sources: list[SourceReference],
        correlation_id: str,
        actor: str,
    ) -> Candidate:
        self._validate(claim_key, content, sources, correlation_id, actor)
        candidate_id = str(uuid.uuid4())
        now = _now()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO candidates VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
                (candidate_id, claim_key, content, self._sources(sources), correlation_id, now, now),
            )
            self._event(connection, correlation_id, actor, "propose", candidate_id, "completed", 0)
        return Candidate(candidate_id, claim_key, content, tuple(sources), correlation_id, "pending", now, now)

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
            ).fetchone()
        if row is None:
            return None
        return Candidate(
            row[0], row[1], row[2], tuple(self._decode_sources(row[3])),
            row[4], row[5], row[6], row[7],
        )

    def list_candidates(self, *, status: str | None = "pending") -> list[Candidate]:
        with self._connect() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM candidates ORDER BY created_at"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM candidates WHERE status = ? ORDER BY created_at",
                    (status,),
                ).fetchall()
        return [
            Candidate(
                row[0], row[1], row[2], tuple(self._decode_sources(row[3])),
                row[4], row[5], row[6], row[7],
            )
            for row in rows
        ]

    def confirm(self, candidate_id: str, *, actor: str, correlation_id: str) -> ConfirmedMemory:
        self._validate_identity(candidate_id, actor, correlation_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
            ).fetchone()
            if row is None:
                raise MemoryGovernanceError("CANDIDATE_NOT_FOUND", candidate_id)
            if row[5] != "pending":
                raise MemoryGovernanceError("CANDIDATE_NOT_PENDING", row[5])
            current = connection.execute(
                "SELECT * FROM records WHERE claim_key = ? AND status = 'confirmed'", (row[1],)
            ).fetchone()
            if current and self._normalize(current[3]) == self._normalize(row[2]):
                connection.execute(
                    "UPDATE candidates SET status = 'duplicate', updated_at = ? WHERE candidate_id = ?",
                    (_now(), candidate_id),
                )
                self._event(connection, correlation_id, actor, "confirm", candidate_id, "duplicate", current[5])
                return self._record(current)
            if current:
                connection.execute(
                    "UPDATE candidates SET status = 'conflict', updated_at = ? WHERE candidate_id = ?",
                    (_now(), candidate_id),
                )
                self._event(connection, correlation_id, actor, "confirm", candidate_id, "conflict", current[5])
                raise MemoryGovernanceError("MEMORY_CONFLICT", row[1])

        record_id = str(uuid.uuid4())
        sources = self._decode_sources(row[3])
        metadata = self._metadata(record_id, row[1], 1, None, sources, correlation_id)
        semantica_id = self._store_authoritative(row[2], metadata)
        now = _now()
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO records VALUES (?, ?, ?, ?, 'confirmed', ?, ?, ?, NULL, ?, ?)",
                    (record_id, semantica_id, row[1], row[2], 1, row[3], correlation_id, now, now),
                )
                connection.execute(
                    "UPDATE candidates SET status = 'confirmed', updated_at = ? WHERE candidate_id = ?",
                    (now, candidate_id),
                )
                self._event(connection, correlation_id, actor, "confirm", record_id, "completed", 1)
        except Exception:
            self.backend.forget(semantica_id)
            raise
        return ConfirmedMemory(record_id, semantica_id, row[1], row[2], tuple(sources), correlation_id, 1, None, now, now)

    def reject(self, candidate_id: str, *, actor: str, correlation_id: str) -> None:
        self._validate_identity(candidate_id, actor, correlation_id)
        with self._connect() as connection:
            changed = connection.execute(
                "UPDATE candidates SET status = 'rejected', updated_at = ? "
                "WHERE candidate_id = ? AND status IN ('pending', 'conflict')",
                (_now(), candidate_id),
            ).rowcount
            if changed != 1:
                raise MemoryGovernanceError("CANDIDATE_NOT_REJECTABLE", candidate_id)
            self._event(connection, correlation_id, actor, "reject", candidate_id, "completed", 0)

    def correct(
        self,
        record_id: str,
        *,
        content: str,
        sources: list[SourceReference],
        actor: str,
        correlation_id: str,
    ) -> ConfirmedMemory:
        self._validate("correction", content, sources, correlation_id, actor)
        with self._connect() as connection:
            old = connection.execute(
                "SELECT * FROM records WHERE record_id = ? AND status = 'confirmed'", (record_id,)
            ).fetchone()
        if old is None:
            raise MemoryGovernanceError("MEMORY_NOT_CONFIRMED", record_id)
        new_id = str(uuid.uuid4())
        version = old[5] + 1
        metadata = self._metadata(new_id, old[2], version, record_id, sources, correlation_id)
        semantica_id = self._store_authoritative(content, metadata)
        if not self.backend.forget(old[1]):
            self.backend.forget(semantica_id)
            raise MemoryGovernanceError("SEMANTICA_CORRECTION_INCOMPLETE", old[1])
        now = _now()
        with self._connect() as connection:
            connection.execute(
                "UPDATE records SET status = 'superseded', updated_at = ? WHERE record_id = ?",
                (now, record_id),
            )
            connection.execute(
                "INSERT INTO records VALUES (?, ?, ?, ?, 'confirmed', ?, ?, ?, ?, ?, ?)",
                (new_id, semantica_id, old[2], content, version, self._sources(sources), correlation_id, record_id, now, now),
            )
            self._event(connection, correlation_id, actor, "correct", new_id, "completed", version)
        return ConfirmedMemory(new_id, semantica_id, old[2], content, tuple(sources), correlation_id, version, record_id, now, now)

    def delete(self, record_id: str, *, actor: str, correlation_id: str) -> None:
        self._validate_identity(record_id, actor, correlation_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM records WHERE record_id = ? AND status = 'confirmed'", (record_id,)
            ).fetchone()
        if row is None:
            raise MemoryGovernanceError("MEMORY_NOT_CONFIRMED", record_id)
        if not self.backend.forget(row[1]):
            raise MemoryGovernanceError("SEMANTICA_DELETE_FAILED", row[1])
        with self._connect() as connection:
            connection.execute(
                "UPDATE records SET content = NULL, sources = '[]', "
                "status = CASE WHEN record_id = ? THEN 'deleted' ELSE status END, updated_at = ? "
                "WHERE claim_key = ?",
                (record_id, _now(), row[2]),
            )
            self._event(connection, correlation_id, actor, "delete", record_id, "completed", row[5])

    def get(self, record_id: str) -> ConfirmedMemory | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM records WHERE record_id = ? AND status = 'confirmed'", (record_id,)
            ).fetchone()
        if row is None:
            return None
        upstream = self.backend.get(row[1])
        if upstream is None:
            raise MemoryGovernanceError("SEMANTICA_RECORD_MISSING", row[1])
        metadata = upstream.get("metadata", {})
        if metadata.get("record_id") != record_id or metadata.get("version") != row[5]:
            raise MemoryGovernanceError("SEMANTICA_RECORD_MISMATCH", record_id)
        content = upstream.get("content")
        if not isinstance(content, str) or not content.strip():
            raise MemoryGovernanceError("SEMANTICA_RECORD_MISSING", row[1])
        return ConfirmedMemory(
            row[0], row[1], row[2], content, tuple(self._decode_sources(row[6])),
            row[7], row[5], row[8], row[9], row[10],
        )

    def retrieve(self, query: str, limit: int = 5) -> list[ConfirmedMemory]:
        if not query.strip() or not 1 <= limit <= 100:
            raise MemoryGovernanceError("MEMORY_QUERY_INVALID", "query or limit invalid")
        results: list[ConfirmedMemory] = []
        for item in self.backend.retrieve(query, limit * 2):
            metadata = item.get("metadata", {})
            record_id = metadata.get("record_id")
            if not record_id or metadata.get("status") != "confirmed":
                continue
            record = self.get(record_id)
            if record:
                results.append(record)
            if len(results) == limit:
                break
        return results
    def history(self, claim_key: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT record_id, status, version, previous_record_id, created_at, updated_at "
                "FROM records WHERE claim_key = ? ORDER BY version", (claim_key,)
            ).fetchall()
        return [dict(row) for row in rows]

    def export(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT record_id FROM records WHERE status = 'confirmed' AND content IS NOT NULL "
                "ORDER BY claim_key, version"
            ).fetchall()
        exported: list[dict[str, object]] = []
        for row in rows:
            confirmed = self.get(row[0])
            if confirmed is not None:
                exported.append(asdict(confirmed))
        return {"schema_version": 1, "exported_at": _now(), "records": exported}

    def health(self) -> dict[str, Any]:
        upstream = self.backend.health()
        return {
            "schema_version": 1,
            "status": "healthy" if upstream.get("status") == "healthy" else "unavailable",
            "confirmed_authority": CONFIRMED_AUTHORITY,
            "semantica": upstream,
        }

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                  candidate_id TEXT PRIMARY KEY, claim_key TEXT NOT NULL, content TEXT NOT NULL,
                  sources TEXT NOT NULL, correlation_id TEXT NOT NULL, status TEXT NOT NULL,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS records (
                  record_id TEXT PRIMARY KEY, semantica_id TEXT NOT NULL UNIQUE, claim_key TEXT NOT NULL,
                  content TEXT, status TEXT NOT NULL, version INTEGER NOT NULL, sources TEXT NOT NULL,
                  correlation_id TEXT NOT NULL, previous_record_id TEXT, created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_confirmed_claim
                  ON records(claim_key) WHERE status = 'confirmed';
                CREATE TABLE IF NOT EXISTS events (
                  event_id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL, actor TEXT NOT NULL,
                  action TEXT NOT NULL, target_id TEXT NOT NULL, outcome TEXT NOT NULL,
                  version INTEGER NOT NULL, occurred_at TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _normalize(content: str) -> str:
        return " ".join(content.casefold().split())

    @staticmethod
    def _sources(sources: list[SourceReference] | tuple[SourceReference, ...]) -> str:
        return json.dumps([asdict(source) for source in sources], separators=(",", ":"))

    @staticmethod
    def _decode_sources(raw: str) -> list[SourceReference]:
        return [SourceReference(**item) for item in json.loads(raw)]

    @staticmethod
    def _validate(claim_key: str, content: str, sources: list[SourceReference], correlation_id: str, actor: str) -> None:
        if not claim_key.strip() or len(claim_key) > 256 or not content.strip() or len(content) > 65536:
            raise MemoryGovernanceError("MEMORY_INPUT_INVALID", "claim or content invalid")
        if not sources or any(not source.uri.strip() or not source.observed_at.strip() for source in sources):
            raise MemoryGovernanceError("MEMORY_SOURCE_REQUIRED", "at least one valid source is required")
        if not CORRELATION.fullmatch(correlation_id) or not actor.strip():
            raise MemoryGovernanceError("MEMORY_AUDIT_IDENTITY_INVALID", "correlation or actor invalid")

    @staticmethod
    def _validate_identity(target: str, actor: str, correlation_id: str) -> None:
        if not target or not actor.strip() or not CORRELATION.fullmatch(correlation_id):
            raise MemoryGovernanceError("MEMORY_AUDIT_IDENTITY_INVALID", "target, actor, or correlation invalid")

    @staticmethod
    def _metadata(record_id: str, claim_key: str, version: int, previous: str | None, sources: list[SourceReference], correlation_id: str) -> dict[str, Any]:
        return build_confirmed_metadata(
            record_id=record_id,
            claim_key=claim_key,
            version=version,
            previous_record_id=previous,
            sources=sources,
            correlation_id=correlation_id,
        )

    def _store_authoritative(self, content: str, metadata: dict[str, Any]) -> str:
        validate_confirmed_metadata(metadata)
        health = self.backend.health()
        if health.get("status") != "healthy":
            raise MemoryGovernanceError("SEMANTICA_UNAVAILABLE", "confirmed memory authority is unavailable")
        memory_id = self.backend.store(content, metadata)
        if not memory_id:
            raise MemoryGovernanceError("SEMANTICA_STORE_FAILED", "Semantica returned no memory id")
        return memory_id

    @staticmethod
    def _event(connection: sqlite3.Connection, correlation_id: str, actor: str, action: str, target: str, outcome: str, version: int) -> None:
        connection.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), correlation_id, actor, action, target, outcome, version, _now()),
        )

    def _record(self, row: sqlite3.Row) -> ConfirmedMemory:
        return ConfirmedMemory(
            row[0], row[1], row[2], row[3], tuple(self._decode_sources(row[6])),
            row[7], row[5], row[8], row[9], row[10],
        )
