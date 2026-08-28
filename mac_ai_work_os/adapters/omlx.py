"""Honest health and capability adapter for oMLX."""

from __future__ import annotations

import json
import shutil
import socket
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Protocol


class AdapterError(RuntimeError):
    """A classified transport or protocol failure."""

    def __init__(self, code: str, message: str, *, http_status: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class HTTPResult:
    status: int
    body: dict[str, Any]


class Transport(Protocol):
    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> HTTPResult: ...


class UrllibTransport:
    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 3.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> HTTPResult:
        headers = {"Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                try:
                    body = json.loads(raw) if raw else {}
                except json.JSONDecodeError as exc:
                    raise AdapterError("INVALID_JSON", f"{path} returned invalid JSON") from exc
                if not isinstance(body, dict):
                    raise AdapterError("INVALID_SHAPE", f"{path} returned a non-object JSON body")
                return HTTPResult(response.status, body)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            message = raw.decode("utf-8", errors="replace") or str(exc)
            code = "AUTH_REQUIRED" if exc.code in {401, 403} else "HTTP_ERROR"
            raise AdapterError(code, message, http_status=exc.code) from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise AdapterError("TIMEOUT", f"{path} timed out") from exc
            raise AdapterError("UNREACHABLE", f"{path} is unreachable: {reason}") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise AdapterError("TIMEOUT", f"{path} timed out") from exc


@dataclass(frozen=True)
class InstallationEvidence:
    installed: bool
    sources: list[str]


def detect_installation(
    application_paths: tuple[Path, ...] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> InstallationEvidence:
    paths = application_paths or (
        Path("/Applications/oMLX.app"),
        Path.home() / "Applications/oMLX.app",
    )
    sources = [str(path) for path in paths if path.is_dir()]
    executable = which("omlx")
    if executable:
        sources.append(executable)
    return InstallationEvidence(bool(sources), sources)


@dataclass(frozen=True)
class OMLXHealthReport:
    schema_version: int
    component: str
    status: str
    installed: bool
    installation_sources: list[str]
    server_reachable: bool
    shallow_health: bool
    deep_probe_performed: bool
    deep_probe_passed: bool
    models: list[str]
    error: dict[str, Any] | None
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OMLXAdapter:
    def __init__(self, transport: Transport):
        self.transport = transport

    def probe(
        self,
        installation: InstallationEvidence,
        *,
        deep: bool = False,
        model: str | None = None,
    ) -> OMLXHealthReport:
        try:
            health = self.transport.request("GET", "/health")
        except AdapterError as exc:
            status = "not_installed" if not installation.installed else "stopped"
            if exc.code == "AUTH_REQUIRED":
                status = "auth_required"
            elif exc.code not in {"UNREACHABLE", "TIMEOUT"}:
                status = "incompatible"
            return self._report(
                status=status,
                installation=installation,
                server_reachable=exc.code not in {"UNREACHABLE", "TIMEOUT"},
                error=exc,
            )

        health_status = str(health.body.get("status", "")).lower()
        if health.status != 200 or health_status in {"loading", "starting"}:
            return self._report(
                status="starting" if health_status in {"loading", "starting"} else "degraded",
                installation=installation,
                server_reachable=True,
                evidence={"health": health.body},
                error=AdapterError("HEALTH_NOT_READY", f"health status is {health_status or health.status}"),
            )
        if health_status not in {"ok", "healthy"}:
            return self._report(
                status="incompatible",
                installation=installation,
                server_reachable=True,
                evidence={"health": health.body},
                error=AdapterError("UNKNOWN_HEALTH", f"unrecognized health status: {health_status!r}"),
            )

        try:
            model_result = self.transport.request("GET", "/v1/models")
            raw_models = model_result.body.get("data")
            if not isinstance(raw_models, list):
                raise AdapterError("INVALID_MODELS", "/v1/models did not return a data list")
            models = [entry["id"] for entry in raw_models if isinstance(entry, dict) and isinstance(entry.get("id"), str)]
        except AdapterError as exc:
            status = "auth_required" if exc.code == "AUTH_REQUIRED" else "incompatible"
            return self._report(
                status=status,
                installation=installation,
                server_reachable=True,
                shallow_health=False,
                evidence={"health": health.body},
                error=exc,
            )

        evidence = {"health": health.body, "model_count": len(models)}
        if not models:
            return self._report(
                status="healthy_no_models",
                installation=installation,
                server_reachable=True,
                shallow_health=True,
                models=models,
                evidence=evidence,
            )
        if not deep:
            return self._report(
                status="shallow_ready",
                installation=installation,
                server_reachable=True,
                shallow_health=True,
                models=models,
                evidence=evidence,
            )

        selected_model = model or models[0]
        if selected_model not in models:
            return self._report(
                status="incompatible",
                installation=installation,
                server_reachable=True,
                shallow_health=True,
                deep_probe_performed=True,
                models=models,
                evidence=evidence,
                error=AdapterError("MODEL_NOT_FOUND", f"deep-probe model not listed: {selected_model}"),
            )
        try:
            completion = self.transport.request(
                "POST",
                "/v1/chat/completions",
                {
                    "model": selected_model,
                    "messages": [{"role": "user", "content": "Reply with OK."}],
                    "temperature": 0,
                    "max_tokens": 2,
                    "stream": False,
                },
            )
            choices = completion.body.get("choices")
            if not isinstance(choices, list) or not choices:
                raise AdapterError("INVALID_COMPLETION", "deep probe returned no choices")
        except AdapterError as exc:
            return self._report(
                status="degraded",
                installation=installation,
                server_reachable=True,
                shallow_health=True,
                deep_probe_performed=True,
                models=models,
                evidence=evidence,
                error=exc,
            )

        evidence["deep_probe_model"] = selected_model
        return self._report(
            status="ready",
            installation=installation,
            server_reachable=True,
            shallow_health=True,
            deep_probe_performed=True,
            deep_probe_passed=True,
            models=models,
            evidence=evidence,
        )

    @staticmethod
    def _report(
        *,
        status: str,
        installation: InstallationEvidence,
        server_reachable: bool,
        shallow_health: bool = False,
        deep_probe_performed: bool = False,
        deep_probe_passed: bool = False,
        models: list[str] | None = None,
        error: AdapterError | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> OMLXHealthReport:
        error_payload = None
        if error:
            error_payload = {
                "code": error.code,
                "message": error.message,
                "http_status": error.http_status,
            }
        return OMLXHealthReport(
            schema_version=1,
            component="omlx",
            status=status,
            installed=installation.installed,
            installation_sources=installation.sources,
            server_reachable=server_reachable,
            shallow_health=shallow_health,
            deep_probe_performed=deep_probe_performed,
            deep_probe_passed=deep_probe_passed,
            models=models or [],
            error=error_payload,
            evidence=evidence or {},
        )
