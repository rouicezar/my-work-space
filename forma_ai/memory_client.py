"""Loopback HTTP client for the governed-memory service."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


OpenURL = Callable[[urllib.request.Request, float], Any]


class MemoryClientError(RuntimeError):
    def __init__(self, code: str, message: str, *, http_status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status


@dataclass(frozen=True)
class MemoryClient:
    host: str
    port: int
    token: str
    timeout: float = 5.0
    open_url: OpenURL = urllib.request.urlopen

    def health(self, correlation_id: str) -> dict[str, Any]:
        return self._unwrap(self._request("GET", "/v1/memory/health", correlation_id=correlation_id))

    def list_candidates(
        self,
        correlation_id: str,
        *,
        status: str | None = "pending",
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {}
        if status is not None:
            payload["status"] = status
        result = self._unwrap(self._request(
            "POST", "/v1/memory/candidates", payload, correlation_id=correlation_id,
        ))
        if not isinstance(result, list):
            raise MemoryClientError("MEMORY_CLIENT_INVALID", "candidates response must be a list")
        return result

    def get_candidate(self, candidate_id: str, correlation_id: str) -> dict[str, Any]:
        return self._unwrap(self._request(
            "POST",
            "/v1/memory/candidate/get",
            {"candidate_id": candidate_id},
            correlation_id=correlation_id,
        ))

    def propose(
        self,
        *,
        actor: str,
        claim_key: str,
        content: str,
        sources: list[dict[str, str]],
        correlation_id: str,
    ) -> dict[str, Any]:
        return self._unwrap(self._request(
            "POST",
            "/v1/memory/propose",
            {
                "actor": actor,
                "claim_key": claim_key,
                "content": content,
                "sources": sources,
            },
            correlation_id=correlation_id,
        ))

    def confirm(self, *, actor: str, candidate_id: str, correlation_id: str) -> dict[str, Any]:
        return self._unwrap(self._request(
            "POST",
            "/v1/memory/confirm",
            {"actor": actor, "candidate_id": candidate_id},
            correlation_id=correlation_id,
        ))

    def reject(self, *, actor: str, candidate_id: str, correlation_id: str) -> dict[str, Any]:
        return self._unwrap(self._request(
            "POST",
            "/v1/memory/reject",
            {"actor": actor, "candidate_id": candidate_id},
            correlation_id=correlation_id,
        ))

    def export(self, correlation_id: str) -> dict[str, Any]:
        return self._unwrap(self._request(
            "POST", "/v1/memory/export", {}, correlation_id=correlation_id,
        ))

    def get(self, record_id: str, correlation_id: str) -> dict[str, Any]:
        return self._unwrap(self._request(
            "POST", "/v1/memory/get", {"record_id": record_id}, correlation_id=correlation_id,
        ))

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        correlation_id: str,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Correlation-ID": correlation_id,
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"http://{self.host}:{self.port}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with self.open_url(request, timeout=self.timeout) as response:
                raw = response.read(8 * 1024 * 1024)
        except urllib.error.HTTPError as exc:
            code = "MEMORY_SERVICE_UNAVAILABLE"
            try:
                decoded = json.loads(exc.read(1024 * 1024))
                if isinstance(decoded, dict) and isinstance(decoded.get("error"), dict):
                    code = str(decoded["error"].get("code", code))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                pass
            raise MemoryClientError(code, "memory service request failed", http_status=exc.code) from exc
        except (OSError, urllib.error.URLError) as exc:
            raise MemoryClientError("MEMORY_SERVICE_UNAVAILABLE", "memory service is unreachable") from exc
        try:
            decoded = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MemoryClientError("MEMORY_CLIENT_INVALID", "memory service returned non-JSON") from exc
        if not isinstance(decoded, dict):
            raise MemoryClientError("MEMORY_CLIENT_INVALID", "memory service envelope must be an object")
        if "error" in decoded:
            error = decoded["error"]
            code = str(error.get("code", "MEMORY_SERVICE_DENIED")) if isinstance(error, dict) else "MEMORY_SERVICE_DENIED"
            raise MemoryClientError(code, "memory service denied the request")
        return decoded

    @staticmethod
    def _unwrap(envelope: dict[str, Any]) -> Any:
        if "result" not in envelope:
            raise MemoryClientError("MEMORY_CLIENT_INVALID", "memory service response missing result")
        return envelope["result"]
