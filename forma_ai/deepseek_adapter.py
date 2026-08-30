"""Approval-gated DeepSeek Chat Completions transport and normalization."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Protocol

from forma_ai.broker import AuditSink
from forma_ai.cloud_approval import CloudApprovalStore
from forma_ai.cloud_catalog import CloudProvider
from forma_ai.inference_routing import CloudEscalationProposal


class DeepSeekError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class HTTPResponse(Protocol):
    status: int
    headers: object
    def read(self, size: int = -1) -> bytes: ...
    def geturl(self) -> str: ...
    def __enter__(self) -> "HTTPResponse": ...
    def __exit__(self, *args: object) -> None: ...


OpenURL = Callable[..., HTTPResponse]


@dataclass(frozen=True)
class DeepSeekUsage:
    prompt_tokens: int
    prompt_cache_hit_tokens: int
    prompt_cache_miss_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


@dataclass(frozen=True)
class DeepSeekResult:
    model: str
    content: str
    finish_reason: str
    tool_proposals: tuple[dict[str, object], ...]
    usage: DeepSeekUsage


class DeepSeekAdapter:
    def __init__(
        self, provider: CloudProvider, approvals: CloudApprovalStore, audit: AuditSink,
        *, open_url: OpenURL = urllib.request.urlopen, timeout: float = 120.0,
        maximum_response_bytes: int = 8 * 1024 * 1024,
    ):
        if provider.id != "deepseek" or provider.origin != "https://api.deepseek.com":
            raise DeepSeekError("DEEPSEEK_PROVIDER_INVALID", provider.id)
        if timeout <= 0 or maximum_response_bytes <= 0:
            raise ValueError("transport limits must be positive")
        self.provider = provider
        self.approvals = approvals
        self.audit = audit
        self.open_url = open_url
        self.timeout = timeout
        self.maximum_response_bytes = maximum_response_bytes

    def execute(
        self, proposal: CloudEscalationProposal, payload: bytes, *, api_key: str,
        now: datetime,
    ) -> DeepSeekResult:
        if not api_key or "\r" in api_key or "\n" in api_key:
            raise DeepSeekError("DEEPSEEK_CREDENTIAL_INVALID", "API key is unavailable")
        approval = self.approvals.consume(proposal, payload, now=now)
        endpoint = self.provider.origin + "/chat/completions"
        request = urllib.request.Request(
            endpoint, data=payload, method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "FormaAI/0.1",
            },
        )
        outcome = "failed"
        error_code: str | None = None
        error_type: str | None = None
        try:
            try:
                with self.open_url(request, timeout=self.timeout) as response:
                    if response.geturl() != endpoint:
                        raise DeepSeekError("DEEPSEEK_REDIRECT_DENIED", response.geturl())
                    if response.status != 200:
                        raise DeepSeekError(_status_code(response.status), str(response.status))
                    content_type = str(response.headers.get("Content-Type", ""))  # type: ignore[attr-defined]
                    if not content_type.lower().startswith("application/json"):
                        raise DeepSeekError("DEEPSEEK_CONTENT_TYPE_INVALID", content_type)
                    raw = response.read(self.maximum_response_bytes + 1)
            except urllib.error.HTTPError as exc:
                raise DeepSeekError(_status_code(exc.code), str(exc.code)) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise DeepSeekError("DEEPSEEK_TRANSPORT_FAILED", type(exc).__name__) from exc
            if len(raw) > self.maximum_response_bytes:
                raise DeepSeekError("DEEPSEEK_RESPONSE_TOO_LARGE", str(len(raw)))
            result = self._normalize(raw, proposal, now)
            outcome = "completed"
            return result
        except DeepSeekError as exc:
            error_code = exc.code
            error_type = type(exc).__name__
            raise
        except Exception as exc:
            error_code = "DEEPSEEK_UNEXPECTED_FAILURE"
            error_type = type(exc).__name__
            raise DeepSeekError(error_code, error_type) from exc
        finally:
            self.audit.record({
                "schema_version": 1, "event": "cloud_inference",
                "correlation_id": proposal.correlation_id,
                "proposal_id": proposal.proposal_id,
                "provider": proposal.provider_id, "model": proposal.model_id,
                "payload_sha256": proposal.payload_sha256,
                "payload_size_bytes": proposal.payload_size_bytes,
                "maximum_output_tokens": proposal.maximum_output_tokens,
                "maximum_cost_usd": approval.maximum_cost_usd,
                "outcome": outcome, "error_code": error_code, "error_type": error_type,
            })

    def _normalize(
        self, raw: bytes, proposal: CloudEscalationProposal, now: datetime,
    ) -> DeepSeekResult:
        try:
            data = json.loads(raw)
            choice = data["choices"][0]
            message = choice["message"]
            usage = data["usage"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise DeepSeekError("DEEPSEEK_RESPONSE_INVALID", "response shape") from exc
        if data.get("model") != proposal.model_id:
            raise DeepSeekError("DEEPSEEK_MODEL_MISMATCH", str(data.get("model")))
        content = message.get("content")
        tools = message.get("tool_calls", [])
        if not isinstance(content, str) or not content.strip() or not isinstance(tools, list):
            raise DeepSeekError("DEEPSEEK_RESPONSE_INVALID", "content or tools")
        names = (
            "prompt_tokens", "completion_tokens", "total_tokens",
        )
        if any(isinstance(usage.get(name), bool) or not isinstance(usage.get(name), int) or usage[name] < 0 for name in names):
            raise DeepSeekError("DEEPSEEK_USAGE_INVALID", "token usage")
        hit = usage.get("prompt_cache_hit_tokens", 0)
        miss = usage.get("prompt_cache_miss_tokens", usage["prompt_tokens"])
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (hit, miss)):
            raise DeepSeekError("DEEPSEEK_USAGE_INVALID", "cache usage")
        if hit + miss != usage["prompt_tokens"] or usage["prompt_tokens"] + usage["completion_tokens"] != usage["total_tokens"]:
            raise DeepSeekError("DEEPSEEK_USAGE_INVALID", "inconsistent totals")
        prices = self.provider.model(proposal.model_id).prices
        peak = self.provider.is_peak(now)
        cost = (
            hit * (prices.cache_hit_peak if peak else prices.cache_hit_off_peak)
            + miss * (prices.cache_miss_peak if peak else prices.cache_miss_off_peak)
            + usage["completion_tokens"] * (prices.output_peak if peak else prices.output_off_peak)
        ) / 1_000_000
        finish = choice.get("finish_reason")
        if not isinstance(finish, str):
            raise DeepSeekError("DEEPSEEK_RESPONSE_INVALID", "finish reason")
        return DeepSeekResult(
            proposal.model_id, content, finish, tuple(tools),
            DeepSeekUsage(usage["prompt_tokens"], hit, miss, usage["completion_tokens"],
                          usage["total_tokens"], round(cost, 8)),
        )


def _status_code(status: int) -> str:
    return {
        400: "DEEPSEEK_INVALID_FORMAT", 401: "DEEPSEEK_AUTH_FAILED",
        402: "DEEPSEEK_INSUFFICIENT_BALANCE", 422: "DEEPSEEK_INVALID_PARAMETERS",
        429: "DEEPSEEK_RATE_LIMITED", 500: "DEEPSEEK_SERVER_ERROR",
        503: "DEEPSEEK_OVERLOADED",
    }.get(status, "DEEPSEEK_HTTP_ERROR")
