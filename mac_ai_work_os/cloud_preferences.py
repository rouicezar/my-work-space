"""Private, default-disabled cloud route selection separate from credentials."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from mac_ai_work_os.cloud_catalog import CloudCatalogError, CloudProvider
from mac_ai_work_os.models import _atomic_json


@dataclass(frozen=True)
class CloudPreferenceState:
    schema_version: int
    enabled: bool
    provider_id: str | None
    model_id: str | None
    valid: bool
    code: str
    updated_at: str | None


class CloudPreferenceStore:
    def __init__(self, product_root: Path):
        if not product_root.is_absolute():
            raise ValueError("product root must be absolute")
        self.directory = product_root / "config"
        self.path = self.directory / "cloud-preferences.json"

    def load(self, provider: CloudProvider | None = None) -> CloudPreferenceState:
        if not self.path.exists() and not self.path.is_symlink():
            return CloudPreferenceState(1, False, None, None, True, "CLOUD_DISABLED_DEFAULT", None)
        if (
            not self.path.is_file() or self.path.is_symlink()
            or stat.S_IMODE(self.path.stat().st_mode) & 0o077
        ):
            return CloudPreferenceState(1, False, None, None, False, "CLOUD_PREFERENCES_UNSAFE", None)
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or set(raw) != {
                "schema_version", "enabled", "provider_id", "model_id", "updated_at",
            }:
                raise ValueError("schema")
            if raw["schema_version"] != 1 or not isinstance(raw["enabled"], bool):
                raise ValueError("values")
            datetime.fromisoformat(raw["updated_at"])
            if raw["enabled"]:
                if provider is None or raw["provider_id"] != provider.id:
                    raise ValueError("provider")
                provider.model(raw["model_id"])
            elif raw["provider_id"] is not None or raw["model_id"] is not None:
                raise ValueError("disabled fields")
        except (OSError, TypeError, ValueError, json.JSONDecodeError, CloudCatalogError):
            return CloudPreferenceState(1, False, None, None, False, "CLOUD_PREFERENCES_INVALID", None)
        return CloudPreferenceState(
            1, raw["enabled"], raw["provider_id"], raw["model_id"], True,
            "CLOUD_ENABLED" if raw["enabled"] else "CLOUD_DISABLED", raw["updated_at"],
        )

    def save(
        self, *, enabled: bool, provider: CloudProvider | None = None,
        model_id: str | None = None, now: datetime,
    ) -> CloudPreferenceState:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be boolean")
        if enabled:
            if provider is None or model_id is None:
                raise ValueError("enabled cloud requires provider and model")
            provider.model(model_id)
            provider_id = provider.id
        else:
            if provider is not None or model_id is not None:
                raise ValueError("disabled cloud must not retain a route")
            provider_id = None
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.directory.is_symlink() or not self.directory.is_dir():
            raise ValueError("cloud preference directory is unsafe")
        os.chmod(self.directory, 0o700)
        state = CloudPreferenceState(
            1, enabled, provider_id, model_id, True,
            "CLOUD_ENABLED" if enabled else "CLOUD_DISABLED",
            now.astimezone(timezone.utc).isoformat(),
        )
        persisted = asdict(state)
        persisted.pop("valid")
        persisted.pop("code")
        _atomic_json(self.path, persisted)
        return state
