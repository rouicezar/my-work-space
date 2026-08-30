"""Strict product-owned capability profiles for verified local models."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
CAPABILITIES = frozenset({"chat", "json", "tools", "vision"})
VALIDATORS = frozenset({"nonempty-text-v1"})
EVIDENCE_STATUSES = frozenset({
    "provisional_single_machine", "verified_single_machine", "verified_multi_machine",
})


class LocalProfileError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class VerifiedLocalProfile:
    id: str
    model_definition_id: str
    runtime_model_ids: frozenset[str]
    hardware_profile_ids: frozenset[str]
    capabilities: frozenset[str]
    context_window_tokens: int
    maximum_output_tokens: int
    minimum_available_memory_mb: int
    validator: str
    evidence_status: str
    evidence_path: str


def load_local_profile(
    path: Path, profile_id: str, *, known_model_ids: frozenset[str],
    known_hardware_profile_ids: frozenset[str], repository_root: Path,
) -> VerifiedLocalProfile:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalProfileError("LOCAL_PROFILE_CATALOG_INVALID", str(path)) from exc
    if not isinstance(data, dict) or set(data) != {"schema_version", "profiles"} or data.get("schema_version") != 1:
        raise LocalProfileError("LOCAL_PROFILE_CATALOG_SCHEMA", str(path))
    profiles = data.get("profiles")
    if not isinstance(profiles, list):
        raise LocalProfileError("LOCAL_PROFILE_CATALOG_SCHEMA", "profiles")
    matches = [item for item in profiles if isinstance(item, dict) and item.get("id") == profile_id]
    if len(matches) != 1:
        raise LocalProfileError("LOCAL_PROFILE_NOT_FOUND", profile_id)
    raw = matches[0]
    expected = {
        "id", "model_definition_id", "runtime_model_ids", "hardware_profile_ids", "capabilities",
        "context_window_tokens", "maximum_output_tokens", "minimum_available_memory_mb",
        "validator", "evidence_status", "evidence_path",
    }
    if set(raw) != expected or not IDENTIFIER.fullmatch(str(raw.get("id", ""))):
        raise LocalProfileError("LOCAL_PROFILE_INVALID", profile_id)
    model_id = raw["model_definition_id"]
    runtime_models = raw["runtime_model_ids"]
    hardware = raw["hardware_profile_ids"]
    capabilities = raw["capabilities"]
    if model_id not in known_model_ids:
        raise LocalProfileError("LOCAL_PROFILE_MODEL_UNKNOWN", str(model_id))
    if (
        not isinstance(runtime_models, list) or not runtime_models
        or any(not isinstance(item, str) or not item.strip() or len(item) > 160 for item in runtime_models)
        or len(runtime_models) != len(set(runtime_models))
    ):
        raise LocalProfileError("LOCAL_PROFILE_RUNTIME_MODEL_INVALID", profile_id)
    if (
        not isinstance(hardware, list) or not hardware
        or any(item not in known_hardware_profile_ids for item in hardware)
        or len(hardware) != len(set(hardware))
    ):
        raise LocalProfileError("LOCAL_PROFILE_HARDWARE_UNKNOWN", profile_id)
    if (
        not isinstance(capabilities, list) or not capabilities
        or any(item not in CAPABILITIES for item in capabilities)
        or len(capabilities) != len(set(capabilities))
    ):
        raise LocalProfileError("LOCAL_PROFILE_CAPABILITIES_INVALID", profile_id)
    numbers = tuple(raw[name] for name in (
        "context_window_tokens", "maximum_output_tokens", "minimum_available_memory_mb",
    ))
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in numbers):
        raise LocalProfileError("LOCAL_PROFILE_LIMIT_INVALID", profile_id)
    if numbers[1] > numbers[0]:
        raise LocalProfileError("LOCAL_PROFILE_LIMIT_INVALID", profile_id)
    if raw["validator"] not in VALIDATORS or raw["evidence_status"] not in EVIDENCE_STATUSES:
        raise LocalProfileError("LOCAL_PROFILE_EVIDENCE_INVALID", profile_id)
    evidence = raw["evidence_path"]
    if not isinstance(evidence, str) or Path(evidence).is_absolute() or ".." in Path(evidence).parts:
        raise LocalProfileError("LOCAL_PROFILE_EVIDENCE_INVALID", profile_id)
    evidence_file = repository_root / evidence
    if not evidence_file.is_file() or evidence_file.is_symlink():
        raise LocalProfileError("LOCAL_PROFILE_EVIDENCE_MISSING", evidence)
    return VerifiedLocalProfile(
        id=raw["id"], model_definition_id=model_id,
        runtime_model_ids=frozenset(runtime_models),
        hardware_profile_ids=frozenset(hardware), capabilities=frozenset(capabilities),
        context_window_tokens=numbers[0], maximum_output_tokens=numbers[1],
        minimum_available_memory_mb=numbers[2], validator=raw["validator"],
        evidence_status=raw["evidence_status"], evidence_path=evidence,
    )
