"""Authenticated loopback service for the governed-memory contract."""

from __future__ import annotations

import hmac
import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit

from forma_ai.broker import AuditSink, BrokerRequest, BrokerResponse
from forma_ai.governed_memory import (
    CORRELATION,
    GovernedMemory,
    MemoryGovernanceError,
    SourceReference,
)


ROUTES = {
    ("GET", "/live"),
    ("GET", "/v1/memory/health"),
    ("POST", "/v1/memory/propose"),
    ("POST", "/v1/memory/confirm"),
    ("POST", "/v1/memory/reject"),
    ("POST", "/v1/memory/correct"),
    ("POST", "/v1/memory/delete"),
    ("POST", "/v1/memory/get"),
    ("POST", "/v1/memory/retrieve"),
    ("POST", "/v1/memory/history"),
    ("POST", "/v1/memory/export"),
}


@dataclass(frozen=True)
class MemoryServicePolicy:
    client_token: str = field(repr=False)
    max_body_bytes: int = 1_048_576
    max_concurrent_requests: int = 8

    def __post_init__(self) -> None:
        if len(self.client_token) < 32:
            raise ValueError("memory service token must contain at least 32 characters")
        if self.max_body_bytes < 1 or self.max_concurrent_requests < 1:
            raise ValueError("memory service resource limits must be positive")


class GovernedMemoryService:
    def __init__(self, policy: MemoryServicePolicy, memory: GovernedMemory, audit: AuditSink):
        self.policy = policy
        self.memory = memory
        self.audit = audit
        self._request_slots = threading.BoundedSemaphore(policy.max_concurrent_requests)
        self._mutation_lock = threading.RLock()

    def handle(self, request: BrokerRequest) -> BrokerResponse:
        started = time.monotonic()
        method = request.method.upper()
        parsed = urlsplit(request.target)
        correlation = self._header(request.headers, "X-Correlation-ID")
        correlation_id = correlation if correlation and CORRELATION.fullmatch(correlation) else str(uuid.uuid4())
        status = 500
        outcome = "internal_error"
        try:
            if parsed.query or parsed.fragment or (method, parsed.path) not in ROUTES:
                status, outcome = 404, "route_denied"
                return self._json(status, {"error": {"code": "ROUTE_DENIED"}}, correlation_id)
            expected = f"Bearer {self.policy.client_token}"
            if not hmac.compare_digest(self._header(request.headers, "Authorization") or "", expected):
                status, outcome = 401, "auth_denied"
                return self._json(status, {"error": {"code": "AUTH_REQUIRED"}}, correlation_id)
            body_bytes = request.declared_body_bytes if request.declared_body_bytes is not None else len(request.body)
            if body_bytes > self.policy.max_body_bytes:
                status, outcome = 413, "body_too_large"
                return self._json(status, {"error": {"code": "BODY_TOO_LARGE"}}, correlation_id)
            payload: dict[str, Any] = {}
            if method == "POST":
                content_type = (self._header(request.headers, "Content-Type") or "").split(";", 1)[0].strip().lower()
                try:
                    decoded = json.loads(request.body)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    decoded = None
                if content_type != "application/json" or not isinstance(decoded, dict):
                    status, outcome = 400, "invalid_json"
                    return self._json(status, {"error": {"code": "INVALID_JSON"}}, correlation_id)
                payload = decoded
            acquired = self._request_slots.acquire(blocking=False)
            if not acquired:
                status, outcome = 503, "service_busy"
                return self._json(status, {"error": {"code": "MEMORY_SERVICE_BUSY"}}, correlation_id)
            try:
                with self._mutation_lock:
                    result = self._dispatch(method, parsed.path, payload, correlation_id)
                status, outcome = 200, "completed"
                return self._json(status, {"schema_version": 1, "correlation_id": correlation_id, "result": result}, correlation_id)
            except MemoryGovernanceError as exc:
                status = self._error_status(exc.code)
                outcome = "governance_denied" if status < 500 else "capability_unavailable"
                return self._json(status, {"error": {"code": exc.code}}, correlation_id)
            except Exception:
                status, outcome = 500, "internal_error"
                return self._json(status, {"error": {"code": "MEMORY_SERVICE_INTERNAL"}}, correlation_id)
            finally:
                self._request_slots.release()
        finally:
            self.audit.record({
                "schema_version": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "memory_service_request",
                "correlation_id": correlation_id,
                "method": method,
                "path": parsed.path,
                "request_bytes": request.declared_body_bytes if request.declared_body_bytes is not None else len(request.body),
                "status": status,
                "outcome": outcome,
                "duration_ms": round((time.monotonic() - started) * 1000, 3),
            })

    def _dispatch(self, method: str, path: str, payload: dict[str, Any], correlation_id: str) -> Any:
        if method == "GET" and path == "/live":
            return {"status": "ok"}
        if method == "GET" and path == "/v1/memory/health":
            return self.memory.health()
        actor = self._required_text(payload, "actor") if path not in {
            "/v1/memory/get", "/v1/memory/retrieve", "/v1/memory/history", "/v1/memory/export"
        } else None
        if path == "/v1/memory/propose":
            return asdict(self.memory.propose(
                claim_key=self._required_text(payload, "claim_key"),
                content=self._required_text(payload, "content"),
                sources=self._sources(payload), correlation_id=correlation_id, actor=actor or "",
            ))
        if path == "/v1/memory/confirm":
            return asdict(self.memory.confirm(self._required_text(payload, "candidate_id"), actor=actor or "", correlation_id=correlation_id))
        if path == "/v1/memory/reject":
            self.memory.reject(self._required_text(payload, "candidate_id"), actor=actor or "", correlation_id=correlation_id)
            return {"status": "rejected"}
        if path == "/v1/memory/correct":
            return asdict(self.memory.correct(
                self._required_text(payload, "record_id"), content=self._required_text(payload, "content"),
                sources=self._sources(payload), actor=actor or "", correlation_id=correlation_id,
            ))
        if path == "/v1/memory/delete":
            self.memory.delete(self._required_text(payload, "record_id"), actor=actor or "", correlation_id=correlation_id)
            return {"status": "deleted"}
        if path == "/v1/memory/get":
            item = self.memory.get(self._required_text(payload, "record_id"))
            return asdict(item) if item else None
        if path == "/v1/memory/retrieve":
            query = self._required_text(payload, "query")
            limit = payload.get("limit", 5)
            if not isinstance(limit, int):
                raise MemoryGovernanceError("MEMORY_QUERY_INVALID", "limit invalid")
            return [asdict(item) for item in self.memory.retrieve(query, limit)]
        if path == "/v1/memory/history":
            return self.memory.history(self._required_text(payload, "claim_key"))
        if path == "/v1/memory/export":
            return self.memory.export()
        raise MemoryGovernanceError("MEMORY_ROUTE_INVALID", path)

    @staticmethod
    def _required_text(payload: dict[str, Any], name: str) -> str:
        value = payload.get(name)
        if not isinstance(value, str) or not value.strip():
            raise MemoryGovernanceError("MEMORY_INPUT_INVALID", name)
        return value

    @staticmethod
    def _sources(payload: dict[str, Any]) -> list[SourceReference]:
        raw = payload.get("sources")
        if not isinstance(raw, list):
            raise MemoryGovernanceError("MEMORY_SOURCE_REQUIRED", "sources")
        try:
            return [SourceReference(**item) for item in raw if isinstance(item, dict)]
        except TypeError as exc:
            raise MemoryGovernanceError("MEMORY_SOURCE_REQUIRED", "sources") from exc

    @staticmethod
    def _error_status(code: str) -> int:
        if code in {"SEMANTICA_UNAVAILABLE", "SEMANTICA_STORE_FAILED"}:
            return 503
        if code in {"CANDIDATE_NOT_FOUND", "MEMORY_NOT_CONFIRMED"}:
            return 404
        if code in {"MEMORY_CONFLICT", "CANDIDATE_NOT_PENDING", "CANDIDATE_NOT_REJECTABLE"}:
            return 409
        return 422

    @staticmethod
    def _header(headers: dict[str, str], name: str) -> str | None:
        target = name.casefold()
        return next((value for key, value in headers.items() if key.casefold() == target), None)

    @staticmethod
    def _json(status: int, body: dict[str, Any], correlation_id: str) -> BrokerResponse:
        return BrokerResponse(status, {
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        }, json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def make_handler(service: GovernedMemoryService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch()

        def do_POST(self) -> None:
            self._dispatch()

        def _dispatch(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = service.policy.max_body_bytes + 1
            if length < 0:
                length = service.policy.max_body_bytes + 1
            body = self.rfile.read(length) if 0 < length <= service.policy.max_body_bytes else b""
            response = service.handle(BrokerRequest(
                self.command, self.path, dict(self.headers.items()), body,
                declared_body_bytes=length,
            ))
            self.send_response(response.status)
            for name, value in response.headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            if response.body:
                self.wfile.write(response.body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def create_memory_server(host: str, port: int, service: GovernedMemoryService) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("memory service must bind to literal IPv4 loopback 127.0.0.1")
    return ThreadingHTTPServer((host, port), make_handler(service))
