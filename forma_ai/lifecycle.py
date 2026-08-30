"""Crash-recoverable lifecycle operation journal.

This module does not install or execute upstream software. It owns the durable,
auditable state transitions that adapters will use in later phases.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL_PHASES = {"completed", "failed"}


class LifecycleError(RuntimeError):
    """Raised for an invalid or unsafe lifecycle transition."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class OperationState:
    schema_version: int
    operation_id: str
    kind: str
    phase: str
    steps: list[str]
    completed_steps: list[str] = field(default_factory=list)
    active_step: str | None = None
    revision: int = 0
    error: dict[str, str] | None = None
    data_policy: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationState":
        return cls(**data)


class LifecycleJournal:
    """Atomic state snapshot plus append-only JSONL event log."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.state_path = directory / "operation.json"
        self.events_path = directory / "events.jsonl"

    def begin(self, kind: str, steps: list[str], data_policy: str | None = None) -> OperationState:
        if kind not in {"install", "uninstall", "update", "repair"}:
            raise LifecycleError(f"unsupported lifecycle operation: {kind}")
        if not steps or len(steps) != len(set(steps)):
            raise LifecycleError("steps must be non-empty and unique")
        existing = self.load_optional()
        if existing and existing.phase not in TERMINAL_PHASES:
            if existing.kind == kind and existing.steps == steps and existing.data_policy == data_policy:
                return existing
            raise LifecycleError("another lifecycle operation is still active")
        if kind == "uninstall" and data_policy not in {"keep", "export", "delete"}:
            raise LifecycleError("uninstall requires keep, export, or delete data policy")

        state = OperationState(
            schema_version=1,
            operation_id=str(uuid.uuid4()),
            kind=kind,
            phase="pending",
            steps=list(steps),
            data_policy=data_policy,
        )
        self._persist(state, "operation_begun", {"kind": kind, "data_policy": data_policy})
        return state

    def start_next(self) -> OperationState:
        state = self.load()
        if state.phase in TERMINAL_PHASES:
            raise LifecycleError(f"operation is already {state.phase}")
        if state.active_step:
            return state
        pending = [step for step in state.steps if step not in state.completed_steps]
        if not pending:
            state.phase = "completed"
            self._persist(state, "operation_completed", {})
            return state
        state.phase = "running"
        state.active_step = pending[0]
        self._persist(state, "step_started", {"step": state.active_step})
        return state

    def complete_active(self) -> OperationState:
        state = self.load()
        if state.phase != "running" or not state.active_step:
            raise LifecycleError("no active step to complete")
        step = state.active_step
        if step not in state.completed_steps:
            state.completed_steps.append(step)
        state.active_step = None
        self._persist(state, "step_completed", {"step": step})
        if len(state.completed_steps) == len(state.steps):
            state.phase = "completed"
            self._persist(state, "operation_completed", {})
        return state

    def fail_active(self, code: str, message: str) -> OperationState:
        state = self.load()
        if state.phase != "running" or not state.active_step:
            raise LifecycleError("no active step to fail")
        state.phase = "failed"
        state.error = {"code": code, "message": message, "step": state.active_step}
        self._persist(state, "operation_failed", dict(state.error))
        return state

    def resume_failed(self) -> OperationState:
        state = self.load()
        if state.phase != "failed" or not state.active_step:
            raise LifecycleError("only a failed operation with an active step can resume")
        state.phase = "running"
        state.error = None
        self._persist(state, "operation_resumed", {"step": state.active_step})
        return state

    def load(self) -> OperationState:
        state = self.load_optional()
        if state is None:
            raise LifecycleError("no lifecycle operation exists")
        return state

    def load_optional(self) -> OperationState | None:
        if not self.state_path.exists():
            return None
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return OperationState.from_dict(data)

    def events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        return [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines()]

    def _persist(self, state: OperationState, event: str, details: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        state.revision += 1
        state.updated_at = utc_now()
        snapshot = json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(prefix="operation-", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(snapshot)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.state_path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

        record = {
            "schema_version": 1,
            "sequence": state.revision,
            "timestamp": state.updated_at,
            "operation_id": state.operation_id,
            "event": event,
            "details": details,
        }
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
