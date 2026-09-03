"""Supervisor and native UI binding for governed-memory review over loopback."""

from __future__ import annotations

from typing import Any, Mapping

from forma_ai.memory_client import MemoryClient, MemoryClientError


MEMORY_REVIEW_AUDIT_PATH = "logs/audit/memory-review.jsonl"
MEMORY_SERVICE_PORT = 43111
CONFIRMED_AUTHORITY = "semantica"

SUPERVISOR_COMMANDS = {
    "snapshot": "memory-review-snapshot",
    "confirm": "memory-review-confirm",
    "reject": "memory-review-reject",
}

HTTP_ROUTES = {
    "health": ("GET", "/v1/memory/health"),
    "list_candidates": ("POST", "/v1/memory/candidates"),
    "get_candidate": ("POST", "/v1/memory/candidate/get"),
    "confirm": ("POST", "/v1/memory/confirm"),
    "reject": ("POST", "/v1/memory/reject"),
    "export": ("POST", "/v1/memory/export"),
    "get": ("POST", "/v1/memory/get"),
}

UI_STATE_FIELDS = {
    "candidate": {
        "primary_id": "candidate_id",
        "status": "pending",
        "claim_key": "claim_key",
        "content": "content",
        "correlation_id": "correlation_id",
        "sources": "sources",
        "semantica_id": None,
        "record_id": None,
        "version": None,
        "previous_record_id": None,
    },
    "confirmed": {
        "primary_id": "record_id",
        "status": "confirmed",
        "claim_key": "claim_key",
        "content": "content",
        "correlation_id": "correlation_id",
        "sources": "sources",
        "semantica_id": "semantica_id",
        "record_id": "record_id",
        "version": "version",
        "previous_record_id": "previous_record_id",
    },
    "conflict": {
        "primary_id": "candidate_id",
        "status": "conflict",
        "claim_key": "claim_key",
        "content": "content",
        "correlation_id": "correlation_id",
        "sources": "sources",
        "semantica_id": None,
        "record_id": None,
        "version": None,
        "previous_record_id": None,
    },
    "correction": {
        "primary_id": "record_id",
        "status": "confirmed",
        "claim_key": "claim_key",
        "content": "content",
        "correlation_id": "correlation_id",
        "sources": "sources",
        "semantica_id": "semantica_id",
        "record_id": "record_id",
        "version": "version",
        "previous_record_id": "previous_record_id",
    },
    "deleted": {
        "primary_id": "record_id",
        "status": "deleted",
        "claim_key": "claim_key",
        "content": "content",
        "correlation_id": "correlation_id",
        "sources": "sources",
        "semantica_id": "semantica_id",
        "record_id": "record_id",
        "version": "version",
        "previous_record_id": "previous_record_id",
    },
}


def binding_contract() -> dict[str, Any]:
    routes = {
        name: {"method": method, "path": path, "supervisor_command": None}
        for name, (method, path) in HTTP_ROUTES.items()
    }
    routes["list_candidates"]["supervisor_command"] = SUPERVISOR_COMMANDS["snapshot"]
    routes["confirm"]["supervisor_command"] = SUPERVISOR_COMMANDS["confirm"]
    routes["reject"]["supervisor_command"] = SUPERVISOR_COMMANDS["reject"]
    return {
        "schema_version": 1,
        "loopback_port": MEMORY_SERVICE_PORT,
        "audit_path": MEMORY_REVIEW_AUDIT_PATH,
        "confirmed_authority": CONFIRMED_AUTHORITY,
        "supervisor_commands": dict(SUPERVISOR_COMMANDS),
        "http_routes": routes,
        "ui_state_fields": UI_STATE_FIELDS,
    }


def build_review_snapshot(client: MemoryClient, correlation_id: str) -> dict[str, Any]:
    health = client.health(correlation_id)
    pending = client.list_candidates(correlation_id, status="pending")
    export = client.export(correlation_id)
    records = export.get("records", []) if isinstance(export, dict) else []
    if not isinstance(records, list):
        records = []
    return {
        "schema_version": 1,
        "correlation_id": correlation_id,
        "service_health": health,
        "confirmed_authority": health.get("confirmed_authority", CONFIRMED_AUTHORITY),
        "pending_candidates": pending,
        "confirmed_records": records,
        "binding": binding_contract(),
    }


def audit_review_event(
    audit: Any,
    *,
    correlation_id: str,
    event: str,
    command: str,
    outcome: str,
    candidate_id: str | None = None,
    record_id: str | None = None,
    error_code: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "event": event,
        "correlation_id": correlation_id,
        "command": command,
        "outcome": outcome,
        "audit_path": MEMORY_REVIEW_AUDIT_PATH,
        "confirmed_authority": CONFIRMED_AUTHORITY,
    }
    if candidate_id:
        payload["candidate_id"] = candidate_id
    if record_id:
        payload["record_id"] = record_id
    if error_code:
        payload["error_code"] = error_code
    if extra:
        payload.update(dict(extra))
    audit.record(payload)


def memory_client_error_code(exc: BaseException) -> str:
    if isinstance(exc, MemoryClientError):
        return exc.code
    return "MEMORY_REVIEW_FAILED"
