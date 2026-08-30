"""Product manifest loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ManifestError(ValueError):
    """Raised when the product manifest violates a lifecycle invariant."""


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest(data)
    return data


def validate_manifest(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ManifestError("unsupported product manifest schema")
    components = data.get("components")
    if not isinstance(components, list) or not components:
        raise ManifestError("components must be a non-empty list")

    ids = [item.get("id") for item in components]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ManifestError("component ids must be unique and non-empty")
    expected = {"semantica", "holaos", "herdr", "omlx"}
    if set(ids) != expected:
        raise ManifestError(f"component set must be {sorted(expected)}")

    orders = [item.get("start_order") for item in components]
    if any(not isinstance(value, int) for value in orders) or len(orders) != len(set(orders)):
        raise ManifestError("start_order values must be unique integers")

    ports = [item["port"] for item in components if item.get("port") is not None]
    if len(ports) != len(set(ports)):
        raise ManifestError("component ports must not collide")
    if any(not isinstance(port, int) or not 1024 <= port <= 65535 for port in ports):
        raise ManifestError("component ports must be unprivileged TCP ports")

    services = data.get("product_services")
    expected_services = ["inference-broker", "governed-memory-service"]
    if not isinstance(services, list) or [item.get("id") for item in services] != expected_services:
        raise ManifestError(f"product services must be {expected_services}")
    service_ports = [item.get("port") for item in services]
    if any(not isinstance(port, int) or not 1024 <= port <= 65535 for port in service_ports):
        raise ManifestError("product service ports must be unprivileged TCP ports")
    if len(service_ports) != len(set(service_ports)) or any(port in ports for port in service_ports):
        raise ManifestError("product service ports must not collide")
    broker, memory_service = services
    if broker.get("bind_policy") != "loopback-only":
        raise ManifestError("inference broker must be loopback-only")
    if broker.get("secret_policy") != "keychain-runtime-injection":
        raise ManifestError("inference broker secrets must be injected from Keychain")
    if (
        broker.get("real_upstream_contract")
        != "verified-pinned-omlx-qwen3-generation-2026-08-29"
    ):
        raise ManifestError("real oMLX broker contract must match reviewed runtime evidence")
    positive_limits = {
        "max_request_bytes",
        "max_response_bytes",
        "max_concurrent_requests",
        "max_concurrent_inference",
        "inference_requests_per_minute",
        "upstream_timeout_seconds",
    }
    if any(not isinstance(broker.get(name), int) or broker[name] < 1 for name in positive_limits):
        raise ManifestError("inference broker resource limits must be positive integers")
    if broker["max_concurrent_inference"] > broker["max_concurrent_requests"]:
        raise ManifestError("inference concurrency cannot exceed total broker concurrency")
    if memory_service.get("bind_policy") != "loopback-only":
        raise ManifestError("governed memory service must be loopback-only")
    if memory_service.get("secret_policy") != "keychain-runtime-injection":
        raise ManifestError("governed memory service secrets must be injected from Keychain")
    if memory_service.get("contract") != "verified-service-process-and-synthetic-lifecycle-2026-08-30":
        raise ManifestError("governed memory service contract must match reviewed lifecycle evidence")
    if memory_service.get("embedding_contract") != "unavailable-until-approved-local-route":
        raise ManifestError("governed memory service requires an approved local embedding route")

    for item in components:
        if item.get("update_owner") != "product_compatibility_gate":
            raise ManifestError(f"{item['id']} bypasses the product update gate")
        if item.get("allow_self_update") is not False:
            raise ManifestError(f"{item['id']} self-update must be disabled")
        if item.get("health_contract") != "pending-adapter-verification":
            raise ManifestError(
                f"{item['id']} health contract cannot be promoted without adapter evidence"
            )

    omlx = next(item for item in components if item["id"] == "omlx")
    semantica = next(item for item in components if item["id"] == "semantica")
    if omlx.get("deep_health_contract") != "verified-qwen3-0.6b-4bit-generation-2026-08-29":
        raise ManifestError("oMLX deep health contract must match reviewed generation evidence")
    if omlx.get("model_storage_contract") != "verified-pinned-external-reference-2026-08-29":
        raise ManifestError("oMLX model storage contract must match reviewed reference evidence")
    if semantica.get("port") is not None or semantica.get("runtime") != "isolated_python_library":
        raise ManifestError("Semantica must be consumed as an isolated library, not its upstream REST server")
    if semantica.get("upstream_server_contract") != "rejected-fixed-port-and-shallow-health-v0.6.7":
        raise ManifestError("Semantica upstream server boundary must match reviewed v0.6.7 evidence")

    paths = data.get("paths", {})
    required_paths = {"config", "state", "data", "runtimes", "logs", "backups", "cache", "secrets"}
    if set(paths) != required_paths:
        raise ManifestError("managed path classes are incomplete")
    if not str(paths["secrets"]).startswith("keychain://"):
        raise ManifestError("secrets must use macOS Keychain, not a filesystem path")

    lifecycle = data.get("lifecycle", {})
    for operation in ("install_steps", "uninstall_steps"):
        steps = lifecycle.get(operation)
        if not isinstance(steps, list) or not steps or len(steps) != len(set(steps)):
            raise ManifestError(f"{operation} must be a non-empty unique list")


def ordered_components(data: dict[str, Any], reverse: bool = False) -> list[dict[str, Any]]:
    validate_manifest(data)
    return sorted(data["components"], key=lambda item: item["start_order"], reverse=reverse)
