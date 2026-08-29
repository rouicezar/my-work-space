"""Loopback-only, policy-enforcing HTTP broker for oMLX."""

from __future__ import annotations

import hmac
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.parse import urlsplit


CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ALLOWED_ROUTES = {
    ("GET", "/health"),
    ("GET", "/v1/models"),
    ("POST", "/v1/chat/completions"),
}


@dataclass(frozen=True)
class BrokerPolicy:
    client_token: str = field(repr=False)
    allowed_origins: frozenset[str] = field(default_factory=frozenset)
    max_body_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        if len(self.client_token) < 32:
            raise ValueError("broker client token must contain at least 32 characters")
        if self.max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path not in {"", "/"}:
                raise ValueError(f"invalid exact origin: {origin}")


@dataclass(frozen=True)
class BrokerRequest:
    method: str
    target: str
    headers: dict[str, str]
    body: bytes = b""
    declared_body_bytes: int | None = None


@dataclass(frozen=True)
class BrokerResponse:
    status: int
    headers: dict[str, str]
    body: bytes = b""


class Upstream(Protocol):
    def request(self, method: str, path: str, body: bytes, correlation_id: str) -> BrokerResponse: ...


class AuditSink(Protocol):
    def record(self, event: dict[str, Any]) -> None: ...


class JsonlAuditSink:
    """Append one redacted broker decision per line."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def record(self, event: dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                os.write(descriptor, line.encode("utf-8"))
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


class MemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event: dict[str, Any]) -> None:
        self.events.append(event)


class OMLXUpstream:
    """Constrained upstream transport that injects, rather than forwards, auth."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        parsed = urlsplit(base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("oMLX upstream must be loopback HTTP")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(self, method: str, path: str, body: bytes, correlation_id: str) -> BrokerResponse:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Correlation-ID": correlation_id,
        }
        data = None
        if body:
            headers["Content-Type"] = "application/json"
            data = body
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return BrokerResponse(
                    response.status,
                    {"Content-Type": response.headers.get("Content-Type", "application/json")},
                    response.read(),
                )
        except urllib.error.HTTPError as exc:
            return BrokerResponse(
                exc.code,
                {"Content-Type": exc.headers.get("Content-Type", "application/json")},
                exc.read(),
            )


class OMLXBroker:
    def __init__(self, policy: BrokerPolicy, upstream: Upstream, audit: AuditSink):
        self.policy = policy
        self.upstream = upstream
        self.audit = audit

    def handle(self, request: BrokerRequest) -> BrokerResponse:
        started = time.monotonic()
        method = request.method.upper()
        parsed = urlsplit(request.target)
        correlation_id = self._correlation_id(request.headers.get("X-Correlation-ID"))
        origin = request.headers.get("Origin")
        status = 500
        outcome = "internal_error"
        try:
            if parsed.query or parsed.fragment or (method, parsed.path) not in ALLOWED_ROUTES:
                status, outcome = 404, "route_denied"
                return self._json(status, {"error": {"code": "ROUTE_DENIED"}}, correlation_id, origin)
            if origin is not None and origin not in self.policy.allowed_origins:
                status, outcome = 403, "origin_denied"
                return self._json(status, {"error": {"code": "ORIGIN_DENIED"}}, correlation_id, None)
            expected = f"Bearer {self.policy.client_token}"
            if not hmac.compare_digest(request.headers.get("Authorization", ""), expected):
                status, outcome = 401, "auth_denied"
                return self._json(status, {"error": {"code": "AUTH_REQUIRED"}}, correlation_id, origin)
            request_bytes = request.declared_body_bytes if request.declared_body_bytes is not None else len(request.body)
            if request_bytes > self.policy.max_body_bytes:
                status, outcome = 413, "body_too_large"
                return self._json(status, {"error": {"code": "BODY_TOO_LARGE"}}, correlation_id, origin)
            if method == "POST":
                content_type = request.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if content_type != "application/json" or not self._is_json_object(request.body):
                    status, outcome = 400, "invalid_json"
                    return self._json(status, {"error": {"code": "INVALID_JSON"}}, correlation_id, origin)
            response = self.upstream.request(method, parsed.path, request.body, correlation_id)
            status = response.status
            outcome = "forwarded"
            headers = {
                "Content-Type": response.headers.get("Content-Type", "application/json"),
                "X-Correlation-ID": correlation_id,
                "Cache-Control": "no-store",
            }
            if origin is not None:
                headers["Access-Control-Allow-Origin"] = origin
                headers["Vary"] = "Origin"
            return BrokerResponse(status, headers, response.body)
        finally:
            self.audit.record(
                {
                    "schema_version": 1,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "broker_request",
                    "correlation_id": correlation_id,
                    "method": method,
                    "path": parsed.path,
                    "origin_present": origin is not None,
                    "request_bytes": request.declared_body_bytes if request.declared_body_bytes is not None else len(request.body),
                    "status": status,
                    "outcome": outcome,
                    "duration_ms": round((time.monotonic() - started) * 1000, 3),
                }
            )

    def preflight(self, request: BrokerRequest) -> BrokerResponse:
        started = time.monotonic()
        origin = request.headers.get("Origin")
        requested_method = request.headers.get("Access-Control-Request-Method", "").upper()
        requested_headers = {
            item.strip().lower()
            for item in request.headers.get("Access-Control-Request-Headers", "").split(",")
            if item.strip()
        }
        path = urlsplit(request.target).path
        allowed_headers = {"authorization", "content-type", "x-correlation-id"}
        allowed = not (
            origin not in self.policy.allowed_origins
            or (requested_method, path) not in ALLOWED_ROUTES
            or not requested_headers.issubset(allowed_headers)
        )
        correlation_id = self._correlation_id(request.headers.get("X-Correlation-ID"))
        if allowed:
            response = BrokerResponse(
                204,
                {
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": requested_method,
                    "Access-Control-Allow-Headers": ", ".join(sorted(allowed_headers)),
                    "Access-Control-Max-Age": "600",
                    "Vary": "Origin",
                    "Cache-Control": "no-store",
                    "X-Correlation-ID": correlation_id,
                },
            )
        else:
            response = BrokerResponse(403, {"Cache-Control": "no-store", "X-Correlation-ID": correlation_id})
        self.audit.record(
            {
                "schema_version": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "broker_preflight",
                "correlation_id": correlation_id,
                "method": "OPTIONS",
                "path": path,
                "origin_present": origin is not None,
                "request_bytes": 0,
                "status": response.status,
                "outcome": "preflight_allowed" if allowed else "preflight_denied",
                "duration_ms": round((time.monotonic() - started) * 1000, 3),
            }
        )
        return response

    @staticmethod
    def _correlation_id(candidate: str | None) -> str:
        if candidate and CORRELATION_PATTERN.fullmatch(candidate):
            return candidate
        return str(uuid.uuid4())

    @staticmethod
    def _is_json_object(body: bytes) -> bool:
        try:
            return isinstance(json.loads(body), dict)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False

    @staticmethod
    def _json(status: int, body: dict[str, Any], correlation_id: str, origin: str | None) -> BrokerResponse:
        headers = {
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
            "Cache-Control": "no-store",
        }
        if origin is not None:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        return BrokerResponse(status, headers, json.dumps(body).encode("utf-8"))


def make_handler(broker: OMLXBroker) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch()

        def do_POST(self) -> None:
            self._dispatch()

        def do_OPTIONS(self) -> None:
            self._send(broker.preflight(self._request(read_body=False)))

        def _dispatch(self) -> None:
            self._send(broker.handle(self._request(read_body=True)))

        def _request(self, *, read_body: bool) -> BrokerRequest:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = broker.policy.max_body_bytes + 1
            if length < 0:
                length = broker.policy.max_body_bytes + 1
            body = (
                self.rfile.read(length)
                if read_body and 0 < length <= broker.policy.max_body_bytes
                else b""
            )
            return BrokerRequest(
                self.command,
                self.path,
                dict(self.headers.items()),
                body,
                declared_body_bytes=length,
            )

        def _send(self, response: BrokerResponse) -> None:
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


def create_server(host: str, port: int, broker: OMLXBroker) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("broker must bind to loopback")
    return ThreadingHTTPServer((host, port), make_handler(broker))
