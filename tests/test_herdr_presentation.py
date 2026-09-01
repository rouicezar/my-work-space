import unittest

from forma_ai.herdr_adapter import (
    HerdrSessionAgent,
    HerdrSessionSnapshot,
)
from forma_ai.herdr_transport import HerdrTransportError
from forma_ai.herdr_presentation import HerdrPresentationProvider


def snapshot(*, state: str, revision: int) -> HerdrSessionSnapshot:
    return HerdrSessionSnapshot(
        version="0.8.2",
        protocol=20,
        workspaces=(),
        tabs=(),
        panes=(),
        agents=(
            HerdrSessionAgent(
                terminal_id="terminal-1",
                agent_status=state,
                workspace_id="workspace-1",
                tab_id="tab-1",
                pane_id="pane-1",
                focused=True,
                revision=revision,
            ),
        ),
        layouts=(),
    )


class ScriptedAdapter:
    def __init__(self, snapshots, order):
        self.snapshots = iter(snapshots)
        self.order = order

    def snapshot(self):
        self.order.append("snapshot")
        return next(self.snapshots)


class ScriptedListener:
    def __init__(self, *, order, events=(), error=None):
        self.order = order
        self.events = events
        self.error = error

    def subscribe(self, subscriptions, on_event):
        self.order.append("subscribe")
        if subscriptions != [
            {"type": "pane.agent_status_changed", "pane_id": "pane-1"}
        ]:
            raise AssertionError("provider must bind subscriptions to snapshot panes")
        for event in self.events:
            on_event(event)
        if self.error is not None:
            raise self.error


class HerdrPresentationProviderTests(unittest.TestCase):
    def test_forced_loss_invalidates_then_snapshot_reconciles_before_resubscribe(self):
        order = []
        listeners = iter(
            [
                ScriptedListener(
                    order=order,
                    events=(
                        {
                            "event": "pane.agent_status_changed",
                            "data": {
                                "pane_id": "pane-1",
                                "agent_status": "blocked",
                                "revision": 4,
                            },
                        },
                    ),
                    error=HerdrTransportError("forced socket loss"),
                ),
                ScriptedListener(
                    order=order,
                    events=(
                        {
                            "event": "pane.agent_status_changed",
                            "data": {
                                "pane_id": "pane-1",
                                "agent_status": "working",
                                "revision": 7,
                            },
                        },
                    ),
                ),
            ]
        )
        provider = HerdrPresentationProvider(
            adapter=ScriptedAdapter(
                [snapshot(state="working", revision=5), snapshot(state="idle", revision=6)],
                order,
            ),
            listener_factory=lambda: next(listeners),
        )
        updates = []

        provider.run_reconnecting(updates.append, maximum_reconnects=1)

        self.assertEqual(order, ["snapshot", "subscribe", "snapshot", "subscribe"])
        self.assertEqual(
            [(item.freshness, item.agents[0].state, item.agents[0].revision) for item in updates],
            [
                ("fresh", "working", 5),
                ("stale", "unknown", 5),
                ("fresh", "idle", 6),
                ("fresh", "working", 7),
            ],
        )


if __name__ == "__main__":
    unittest.main()
