"""Product-owned policy boundary for delegating execution to Herdr."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from forma_ai.herdr_adapter import HerdrTask


class HerdrTaskSpawner(Protocol):
    def spawn_task(
        self,
        *,
        task_id: str,
        correlation_id: str,
        agent_name: str,
        agent_kind: str,
        pane_id: str,
    ) -> HerdrTask: ...


@dataclass(frozen=True)
class SupervisorFeatures:
    herdr_execution_enabled: bool = False


class SupervisorFeatureUnavailable(RuntimeError):
    """Raised when a caller requests a disabled execution capability."""


class Supervisor:
    """Gate product task dispatch without duplicating Herdr runtime state."""

    def __init__(
        self,
        *,
        features: SupervisorFeatures,
        herdr: HerdrTaskSpawner,
    ) -> None:
        self._features = features
        self._herdr = herdr

    def dispatch_agent_task(
        self,
        *,
        task_id: str,
        correlation_id: str,
        agent_name: str,
        agent_kind: str,
        pane_id: str,
    ) -> HerdrTask:
        if not self._features.herdr_execution_enabled:
            raise SupervisorFeatureUnavailable("HERDR_EXECUTION_DISABLED")
        return self._herdr.spawn_task(
            task_id=task_id,
            correlation_id=correlation_id,
            agent_name=agent_name,
            agent_kind=agent_kind,
            pane_id=pane_id,
        )
