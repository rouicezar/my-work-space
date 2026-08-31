"""Thin discovery boundary for the pinned Herdr runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from shutil import which
from typing import Callable

from .adapter_contract import AdapterIdentity, HealthEnvelope


ExecutableFinder = Callable[[str], str | None]
Clock = Callable[[], str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class HerdrAvailability:
    identity: AdapterIdentity
    installed: bool
    executable_path: str | None
    health: HealthEnvelope


class HerdrAdapter:
    """Discover Herdr without mistaking executable presence for health."""

    def __init__(
        self,
        *,
        executable_finder: ExecutableFinder = which,
        clock: Clock = _utc_now,
    ) -> None:
        self._executable_finder = executable_finder
        self._clock = clock

    def availability(self) -> HerdrAvailability:
        executable_path = self._executable_finder("herdr")
        installed = executable_path is not None

        identity = AdapterIdentity(
            adapter_id="forma.herdr",
            adapter_version="0.1.0",
            protocol_version="1",
            upstream_id="herdr",
            upstream_version="0.8.2",
        )
        health = HealthEnvelope(
            schema_version=1,
            status="unknown" if installed else "unavailable",
            reachable=False,
            ready=False,
            proof="binary_discovered_only" if installed else "binary_not_found",
            checked_at=self._clock(),
            reason_code=(
                "HERDR_HEALTH_NOT_PROBED" if installed else "HERDR_BINARY_NOT_FOUND"
            ),
        )
        return HerdrAvailability(
            identity=identity,
            installed=installed,
            executable_path=executable_path,
            health=health,
        )
