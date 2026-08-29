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
    if not isinstance(services, list) or [item.get("id") for item in services] != ["inference-broker"]:
        raise ManifestError("inference-broker product service is required")
    broker = services[0]
    if broker.get("bind_policy") != "loopback-only":
        raise ManifestError("inference broker must be loopback-only")
    if broker.get("secret_policy") != "keychain-runtime-injection":
        raise ManifestError("inference broker secrets must be injected from Keychain")
    broker_port = broker.get("port")
    if not isinstance(broker_port, int) or not 1024 <= broker_port <= 65535:
        raise ManifestError("inference broker port must be an unprivileged TCP port")
    if broker_port in ports:
        raise ManifestError("inference broker port must not collide with component ports")
    if broker.get("real_upstream_contract") != "verified-pinned-omlx-shallow-2026-08-29":
        raise ManifestError("real oMLX broker contract must match reviewed runtime evidence")

    for item in components:
        if item.get("update_owner") != "product_compatibility_gate":
            raise ManifestError(f"{item['id']} bypasses the product update gate")
        if item.get("allow_self_update") is not False:
            raise ManifestError(f"{item['id']} self-update must be disabled")
        if item.get("health_contract") != "pending-adapter-verification":
            raise ManifestError(
                f"{item['id']} health contract cannot be promoted without adapter evidence"
            )

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
