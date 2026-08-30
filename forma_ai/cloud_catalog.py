"""Strict replaceable catalog for optional cloud inference providers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
CAPABILITIES = frozenset({"chat", "json", "tools", "vision"})


class CloudCatalogError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CloudPrices:
    cache_hit_off_peak: float
    cache_hit_peak: float
    cache_miss_off_peak: float
    cache_miss_peak: float
    output_off_peak: float
    output_peak: float


@dataclass(frozen=True)
class CloudModel:
    id: str
    capabilities: frozenset[str]
    context_window_tokens: int
    maximum_output_tokens: int
    prices: CloudPrices


@dataclass(frozen=True)
class PeakPeriod:
    weekdays: frozenset[int]
    start_minute: int
    end_minute: int


@dataclass(frozen=True)
class CloudProvider:
    id: str
    enabled_by_default: bool
    origin: str
    protocol: str
    models: tuple[CloudModel, ...]
    pricing_source: str
    pricing_effective_at: datetime
    pricing_maximum_age_hours: int
    peak_periods_utc: tuple[PeakPeriod, ...]
    privacy_policy_url: str
    privacy_policy_updated_at: str
    processing_location: str
    retention: str
    training_opt_out_state: str

    def model(self, model_id: str) -> CloudModel:
        matches = [item for item in self.models if item.id == model_id]
        if len(matches) != 1:
            raise CloudCatalogError("CLOUD_MODEL_NOT_FOUND", model_id)
        return matches[0]

    def pricing_is_current(self, now: datetime) -> bool:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        age = now.astimezone(timezone.utc) - self.pricing_effective_at
        return 0 <= age.total_seconds() <= self.pricing_maximum_age_hours * 3600

    def is_peak(self, now: datetime) -> bool:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        current = now.astimezone(timezone.utc)
        minute = current.hour * 60 + current.minute
        return any(
            current.isoweekday() in period.weekdays
            and period.start_minute <= minute < period.end_minute
            for period in self.peak_periods_utc
        )


def load_cloud_provider(path: Path, provider_id: str) -> CloudProvider:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CloudCatalogError("CLOUD_CATALOG_INVALID", str(path)) from exc
    if data.get("schema_version") != 1 or set(data) != {
        "schema_version", "updated_at", "providers",
    }:
        raise CloudCatalogError("CLOUD_CATALOG_SCHEMA", str(path))
    providers = data.get("providers")
    if not isinstance(providers, list):
        raise CloudCatalogError("CLOUD_CATALOG_SCHEMA", "providers")
    matches = [item for item in providers if item.get("id") == provider_id]
    if len(matches) != 1:
        raise CloudCatalogError("CLOUD_PROVIDER_NOT_FOUND", provider_id)
    raw = matches[0]
    required = {
        "id", "enabled_by_default", "origin", "protocol", "models", "pricing", "privacy",
    }
    if set(raw) != required or not IDENTIFIER.fullmatch(str(raw.get("id", ""))):
        raise CloudCatalogError("CLOUD_PROVIDER_INVALID", provider_id)
    if raw["enabled_by_default"] is not False:
        raise CloudCatalogError("CLOUD_PROVIDER_UNSAFE_DEFAULT", provider_id)
    origin = _https_url(raw["origin"], "CLOUD_ORIGIN_INVALID")
    parsed = urlsplit(origin)
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise CloudCatalogError("CLOUD_ORIGIN_INVALID", origin)
    if raw["protocol"] != "openai-chat-completions":
        raise CloudCatalogError("CLOUD_PROTOCOL_UNSUPPORTED", str(raw["protocol"]))
    models = tuple(_model(item) for item in raw["models"])
    if not models or len({item.id for item in models}) != len(models):
        raise CloudCatalogError("CLOUD_MODELS_INVALID", provider_id)
    pricing = raw["pricing"]
    privacy = raw["privacy"]
    if set(pricing) != {
        "source", "effective_at", "maximum_age_hours", "peak_periods_utc",
    } or set(privacy) != {
        "policy_url", "policy_updated_at", "processing_location", "retention",
        "training_opt_out_state",
    }:
        raise CloudCatalogError("CLOUD_POLICY_INVALID", provider_id)
    source = _https_url(pricing["source"], "CLOUD_PRICING_SOURCE_INVALID")
    policy = _https_url(privacy["policy_url"], "CLOUD_PRIVACY_SOURCE_INVALID")
    try:
        effective = datetime.fromisoformat(str(pricing["effective_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise CloudCatalogError("CLOUD_PRICING_TIME_INVALID", provider_id) from exc
    maximum_age = pricing["maximum_age_hours"]
    if isinstance(maximum_age, bool) or not isinstance(maximum_age, int) or maximum_age <= 0:
        raise CloudCatalogError("CLOUD_PRICING_AGE_INVALID", provider_id)
    if privacy["retention"] != "variable" or privacy["training_opt_out_state"] != "unknown":
        raise CloudCatalogError("CLOUD_PRIVACY_CLAIM_UNSAFE", provider_id)
    periods = tuple(_peak_period(item) for item in pricing["peak_periods_utc"])
    if not periods:
        raise CloudCatalogError("CLOUD_PEAK_PERIOD_INVALID", provider_id)
    return CloudProvider(
        id=raw["id"], enabled_by_default=False, origin=origin, protocol=raw["protocol"],
        models=models, pricing_source=source, pricing_effective_at=effective,
        pricing_maximum_age_hours=maximum_age, peak_periods_utc=periods,
        privacy_policy_url=policy,
        privacy_policy_updated_at=str(privacy["policy_updated_at"]),
        processing_location=str(privacy["processing_location"]),
        retention="variable", training_opt_out_state="unknown",
    )


def _model(raw: object) -> CloudModel:
    if not isinstance(raw, dict) or set(raw) != {
        "id", "capabilities", "context_window_tokens", "maximum_output_tokens",
        "pricing_usd_per_million_tokens",
    }:
        raise CloudCatalogError("CLOUD_MODEL_INVALID", str(raw))
    model_id = str(raw["id"])
    capabilities = raw["capabilities"]
    if (
        not IDENTIFIER.fullmatch(model_id) or not isinstance(capabilities, list)
        or not capabilities or any(item not in CAPABILITIES for item in capabilities)
        or len(capabilities) != len(set(capabilities))
    ):
        raise CloudCatalogError("CLOUD_MODEL_INVALID", model_id)
    context = raw["context_window_tokens"]
    output = raw["maximum_output_tokens"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in (context, output)):
        raise CloudCatalogError("CLOUD_MODEL_LIMIT_INVALID", model_id)
    prices = raw["pricing_usd_per_million_tokens"]
    names = tuple(CloudPrices.__dataclass_fields__)
    if not isinstance(prices, dict) or set(prices) != set(names):
        raise CloudCatalogError("CLOUD_PRICE_INVALID", model_id)
    values = [prices[name] for name in names]
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 for value in values):
        raise CloudCatalogError("CLOUD_PRICE_INVALID", model_id)
    return CloudModel(model_id, frozenset(capabilities), context, output, CloudPrices(*values))


def _https_url(value: object, code: str) -> str:
    parsed = urlsplit(str(value))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise CloudCatalogError(code, str(value))
    return str(value)


def _peak_period(raw: object) -> PeakPeriod:
    if not isinstance(raw, dict) or set(raw) != {"weekdays", "start", "end"}:
        raise CloudCatalogError("CLOUD_PEAK_PERIOD_INVALID", str(raw))
    weekdays = raw["weekdays"]
    if (
        not isinstance(weekdays, list) or not weekdays
        or any(isinstance(day, bool) or not isinstance(day, int) or day < 1 or day > 7 for day in weekdays)
        or len(weekdays) != len(set(weekdays))
    ):
        raise CloudCatalogError("CLOUD_PEAK_PERIOD_INVALID", str(raw))
    try:
        start_hour, start_minute = (int(value) for value in str(raw["start"]).split(":"))
        end_hour, end_minute = (int(value) for value in str(raw["end"]).split(":"))
    except (TypeError, ValueError) as exc:
        raise CloudCatalogError("CLOUD_PEAK_PERIOD_INVALID", str(raw)) from exc
    start = start_hour * 60 + start_minute
    end = end_hour * 60 + end_minute
    if not (0 <= start < end <= 1440) or start_minute > 59 or end_minute > 59:
        raise CloudCatalogError("CLOUD_PEAK_PERIOD_INVALID", str(raw))
    return PeakPeriod(frozenset(weekdays), start, end)
