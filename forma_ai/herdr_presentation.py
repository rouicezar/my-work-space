"""Fail-closed presentation projection over Herdr snapshot and event authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from .herdr_adapter import HerdrSessionSnapshot
from .herdr_transport import (
    HerdrProtocolError,
    HerdrRequestError,
    HerdrTransportError,
)


class SnapshotSource(Protocol):
    def snapshot(self) -> HerdrSessionSnapshot: ...


class SubscriptionSource(Protocol):
    def subscribe(
        self,
        subscriptions: list[dict[str, object]],
        on_event: Callable[[dict[str, object]], None],
    ) -> None: ...


@dataclass(frozen=True)
class HerdrPresentedAgent:
    pane_id: str
    terminal_id: str
    workspace_id: str
    tab_id: str
    state: str
    revision: int


@dataclass(frozen=True)
class HerdrPresentation:
    freshness: str
    agents: tuple[HerdrPresentedAgent, ...]
    reason: str | None = None


class HerdrPresentationProvider:
    """Projects Herdr truth and invalidates it before every reconnect.

    Herdr subscriptions do not replay missed events. Recovery therefore always
    obtains a fresh snapshot before opening the next subscription. This object
    owns projection lifecycle only; Herdr remains the runtime state authority.
    """

    def __init__(
        self,
        *,
        adapter: SnapshotSource,
        listener_factory: Callable[[], SubscriptionSource],
    ) -> None:
        self._adapter = adapter
        self._listener_factory = listener_factory
        self._agents: dict[str, HerdrPresentedAgent] = {}

    def run_reconnecting(
        self,
        on_update: Callable[[HerdrPresentation], None],
        *,
        maximum_reconnects: int,
    ) -> None:
        if maximum_reconnects < 0:
            raise ValueError("maximum_reconnects must be nonnegative")
        attempts = 0
        while True:
            self._reconcile_snapshot(self._adapter.snapshot())
            self._publish(on_update, freshness="fresh")
            listener = self._listener_factory()
            try:
                listener.subscribe(
                    [
                        {"type": "pane.agent_status_changed", "pane_id": pane_id}
                        for pane_id in sorted(self._agents)
                    ],
                    lambda event: self._apply_event(event, on_update),
                )
                return
            except (
                HerdrTransportError,
                HerdrProtocolError,
                HerdrRequestError,
                OSError,
            ) as exc:
                self._agents = {
                    pane_id: HerdrPresentedAgent(
                        pane_id=agent.pane_id,
                        terminal_id=agent.terminal_id,
                        workspace_id=agent.workspace_id,
                        tab_id=agent.tab_id,
                        state="unknown",
                        revision=agent.revision,
                    )
                    for pane_id, agent in self._agents.items()
                }
                self._publish(
                    on_update,
                    freshness="stale",
                    reason=type(exc).__name__,
                )
                if attempts >= maximum_reconnects:
                    raise
                attempts += 1

    def _apply_event(
        self,
        event: dict[str, object],
        on_update: Callable[[HerdrPresentation], None],
    ) -> None:
        if event.get("event") != "pane.agent_status_changed":
            return
        data = event.get("data")
        if not isinstance(data, dict):
            return
        pane_id = data.get("pane_id")
        state = data.get("agent_status")
        revision = data.get(
            "revision", data.get("state_change_seq", data.get("seq"))
        )
        if not isinstance(pane_id, str) or not isinstance(state, str):
            return
        if not isinstance(revision, int):
            # v0.8.2 subscription payloads omit revision even though snapshots
            # carry it. Treat the event as an invalidation hint and reconcile
            # from Herdr instead of inventing product-owned ordering.
            self._reconcile_snapshot(self._adapter.snapshot())
            self._publish(on_update, freshness="fresh")
            return
        current = self._agents.get(pane_id)
        if current is None or revision <= current.revision:
            return
        self._agents[pane_id] = HerdrPresentedAgent(
            pane_id=current.pane_id,
            terminal_id=current.terminal_id,
            workspace_id=current.workspace_id,
            tab_id=current.tab_id,
            state=state,
            revision=revision,
        )
        self._publish(on_update, freshness="fresh")

    def _reconcile_snapshot(self, snapshot: HerdrSessionSnapshot) -> None:
        self._agents = {
            item.pane_id: HerdrPresentedAgent(
                pane_id=item.pane_id,
                terminal_id=item.terminal_id,
                workspace_id=item.workspace_id,
                tab_id=item.tab_id,
                state=item.agent_status,
                revision=item.revision,
            )
            for item in snapshot.agents
        }

    def _publish(
        self,
        on_update: Callable[[HerdrPresentation], None],
        *,
        freshness: str,
        reason: str | None = None,
    ) -> None:
        on_update(
            HerdrPresentation(
                freshness=freshness,
                agents=tuple(self._agents[key] for key in sorted(self._agents)),
                reason=reason,
            )
        )
