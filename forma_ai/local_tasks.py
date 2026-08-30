"""Bounded, text-only task contract for the daily local-Qwen path."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


MAXIMUM_TASK_BYTES = 1024 * 1024
MAXIMUM_PROMPT_BYTES = 256 * 1024
MAXIMUM_OUTPUT_TOKENS = 4096


class LocalTaskError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LocalTaskRequest:
    schema_version: int
    prompt: str
    maximum_output_tokens: int


@dataclass(frozen=True)
class LocalTaskResult:
    schema_version: int
    route: str
    correlation_id: str
    model: str
    output: str
    finish_reason: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    audit_path: str


def parse_local_task(data: bytes) -> LocalTaskRequest:
    if not data or len(data) > MAXIMUM_TASK_BYTES:
        raise LocalTaskError("LOCAL_TASK_SIZE_INVALID", str(len(data)))
    try:
        raw = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalTaskError("LOCAL_TASK_JSON_INVALID", "task must be UTF-8 JSON") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "prompt", "maximum_output_tokens",
    }:
        raise LocalTaskError("LOCAL_TASK_SCHEMA_INVALID", "unexpected task fields")
    prompt = raw["prompt"]
    output = raw["maximum_output_tokens"]
    if (
        raw["schema_version"] != 1 or not isinstance(prompt, str)
        or not prompt.strip() or "\x00" in prompt
        or len(prompt.encode("utf-8")) > MAXIMUM_PROMPT_BYTES
    ):
        raise LocalTaskError("LOCAL_TASK_PROMPT_INVALID", "prompt is invalid")
    if isinstance(output, bool) or not isinstance(output, int) or not 1 <= output <= MAXIMUM_OUTPUT_TOKENS:
        raise LocalTaskError("LOCAL_TASK_OUTPUT_LIMIT_INVALID", str(output))
    return LocalTaskRequest(1, prompt, output)


def completion_body(task: LocalTaskRequest, model: str) -> dict[str, Any]:
    if not isinstance(model, str) or not model.strip():
        raise LocalTaskError("LOCAL_MODEL_UNAVAILABLE", "model identifier is unavailable")
    return {
        "model": model,
        "messages": [{"role": "user", "content": task.prompt}],
        "temperature": 0.2,
        "max_tokens": task.maximum_output_tokens,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }


def normalize_local_result(
    response: object, *, correlation_id: str, expected_model: str,
) -> LocalTaskResult:
    try:
        if not isinstance(response, dict):
            raise TypeError("response")
        choice = response["choices"][0]
        content = choice["message"]["content"]
        finish = choice["finish_reason"]
        returned_model = response.get("model", expected_model)
    except (KeyError, IndexError, TypeError) as exc:
        raise LocalTaskError("LOCAL_RESPONSE_INVALID", "response shape") from exc
    if (
        returned_model != expected_model or not isinstance(content, str) or not content.strip()
        or not isinstance(finish, str) or choice["message"].get("tool_calls")
    ):
        raise LocalTaskError("LOCAL_RESPONSE_INVALID", "response contract")
    usage = response.get("usage")
    tokens: tuple[int | None, int | None, int | None] = (None, None, None)
    if usage is not None:
        if not isinstance(usage, dict):
            raise LocalTaskError("LOCAL_USAGE_INVALID", "usage shape")
        values = tuple(usage.get(name) for name in (
            "prompt_tokens", "completion_tokens", "total_tokens",
        ))
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
            raise LocalTaskError("LOCAL_USAGE_INVALID", "token values")
        if values[0] + values[1] != values[2]:
            raise LocalTaskError("LOCAL_USAGE_INVALID", "token totals")
        tokens = values  # type: ignore[assignment]
    return LocalTaskResult(
        1, "local", correlation_id, expected_model, content, finish,
        tokens[0], tokens[1], tokens[2], "logs/audit/inference.jsonl",
    )

