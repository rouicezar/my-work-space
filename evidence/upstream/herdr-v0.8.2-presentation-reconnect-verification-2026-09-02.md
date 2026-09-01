# Herdr v0.8.2 Presentation Reconnect Verification

Date: 2026-09-02 Asia/Shanghai
Task: P3-T13

## Acceptance result

Forma AI now projects Herdr-authoritative agent state through a fail-closed presentation provider. A real server-side socket loss produces `stale` presentation with every previously shown agent changed to `unknown`. Recovery obtains a fresh `session.snapshot` before creating the next `events.subscribe` connection. Old pane identities disappear when the restarted server does not restore them; a newly created authoritative pane is then subscribed and its later `working` transition reaches the provider.

## Upstream facts verified

- Herdr v0.8.2 subscription events are not replayed after disconnect.
- Killing and restarting the server for the same named session does not preserve the old pane/agent identity in this test; the fresh snapshot is therefore empty until a new workspace and agent report exist.
- The live `pane.agent_status_changed` subscription payload contains `pane_id`, `workspace_id`, `agent`, `agent_status`, but no revision or sequence field.
- `session.snapshot` does carry authoritative agent revisions.
- Consequently, an event without revision is treated only as an invalidation hint and immediately reconciled through `session.snapshot`; Forma AI does not invent an ordering value or maintain a competing runtime state machine.
- `events.wait` matches current pane state, while the subscription path remains non-replaying.

## Product binding

- `forma_ai/herdr_presentation.py` owns only projection freshness, snapshot reconciliation, subscription lifecycle, and stale-event rejection.
- `scripts/supervisor.py herdr-snapshot` exposes a versioned one-shot envelope with Herdr version, protocol, freshness, agents, and revisions.
- Swift `RuntimePresentationProvider` maps that envelope and changes all visible agent states to `unknown` on disconnect.
- Runtime presentation has no preview fallback. Actual replacement of preview agent cards is separately owned by P3-T16.

## Verification

- Red: `tests.test_herdr_presentation` initially failed with `ModuleNotFoundError`, proving the provider did not exist.
- Intermediate real failure: server restart returned an empty snapshot, exposing that same-name restart is not old-pane recovery; the test was corrected to require old-pane removal and a new authoritative pane.
- Intermediate real failure: the resumed subscription event had no revision, so the provider correctly refused it; inspection established the actual payload and the implementation changed to snapshot reconciliation rather than fabricated ordering.
- Focused Python: 50 tests passed in 4.433 seconds.
- Full Python: 293 tests passed, 1 expected opt-in Semantica integration skip, in 18.892 seconds.
- Full Swift package: 43 tests passed; 2 environment-gated real Keychain/runtime tests skipped, in 9.484 seconds.
- `git diff --check` passed before commit.

All live Herdr tests use unique disposable named sessions and clean them after execution. No provider credential, cloud call, real external agent session, or default Herdr session was used.
