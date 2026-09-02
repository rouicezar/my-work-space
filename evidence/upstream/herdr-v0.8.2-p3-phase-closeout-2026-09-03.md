# Herdr v0.8.2 P3 Phase Closeout — Real Multi-Agent Loop Verified

Date: 2026-09-03 Asia/Shanghai
Phase: P3 (Herdr-backed multi-agent runtime made real)
Executor: pi agent
Task: P3-T17 (close the real Herdr multi-agent phase)

## Milestone gate

P3 milestone exit gate: *Two parallel tasks run, stream status, cancel, resume, and recover.*

## Evidence

### Full real Herdr integration suite (the four live P3 proofs)

Command: `python3 -m unittest tests.test_herdr_integration -v`

Result: **4 tests OK in 30.391s** against the pinned official binary at `~/Library/Application Support/Forma AI/cache/downloads/herdr-macos-aarch64`, each in a unique disposable named session (`forma-p3t1*-test-<uuid8>`) that self-cleans.

| Test | Covers | Pass |
| --- | --- | --- |
| `HerdrTwoFixtureAgentIntegrationTests.test_two_agents_are_launched_and_detected_by_agent_start` | P3-T12: two provider-free fixtures launched/detected by official `agent.start`; distinct run/pane/terminal identities; parallel work; pane-exact graceful cancel; artifact/output isolation | ✅ |
| `HerdrTwoFixtureAgentIntegrationTests.test_blocked_agent_wait_read_and_explicit_force_close` | P3-T14: real `agent.wait` blocked truth, bounded ANSI-stripped `agent.read`, process reconciliation, graceful interrupt, explicit force-close | ✅ |
| `HerdrDetachReconnectIntegrationTests.test_discarded_client_reclaims_then_starts_explicit_fresh_run` | P3-T15: detach/reconnect; stale-reference reclaim fails closed; explicit `start_fresh_task` with distinct run/pane/terminal identity | ✅ |
| `HerdrEventSubscriptionIntegrationTests.test_live_transitions_subscription_and_reconnect_resubscribe` | P3-T13: snapshot-first presentation; live event subscription; forced socket-loss → stale/unknown → fresh snapshot reconcile → resubscribe | ✅ |

### Whole-project regression

- Full Python suite (`python3 -m unittest discover tests`): **311 tests OK** (1 expected opt-in Semantica skip).
- Full Swift package (`swift test --package-path prototypes/packaging`): **44 tests passed** (2 real-Keychain environment-gated skips).
- Named-session residue: **none** (`~/.config/herdr/sessions/` empty after the run).
- `git diff --check`: clean.

### Manual task review (product CLI path)

Real `scripts/supervisor.py herdr-snapshot --root <product-root>` with no runtime running returns the fail-closed envelope:

```json
{"command": "herdr-snapshot", "status": "ok",
 "payload": {"schema_version": 1, "freshness": "stale",
             "reason": "HERDR_NOT_RUNNING", "version": null,
             "protocol": null, "agents": []}}
```

This proves the real product command does not connect/serve stale data when Herdr is not running; the live-integration suite above proves the authoritative fresh snapshot path against real Herdr.

## Cumulative P3 task status

| Task | Result |
| --- | --- |
| P3-T01..T09 | Adapter contract, thin adapter, spawn/status/cancel/resume mapping, supervisor feature boundary, preview agent cards (verified) |
| P3-T10 | Official pinned Herdr artifact + protocol/schema verified (verified) |
| P3-T11 | Thin adapter bound to official socket transport (verified) |
| P3-T12 | Two real isolated fixture agents through Herdr (verified) |
| P3-T13 | Snapshot + event subscriptions bound; reconnect/resubscribe (verified) |
| P3-T14 | Real wait, blocked, bounded read, two-stage cancellation (verified) |
| P3-T15 | Detach/reconnect and explicit fresh-run recovery (verified) |
| P3-T16 | Real runtime agent cards + Herdr lifecycle management (verified) |
| P3-T17 | Phase closeout: full real integration suite + manual task review (verified) |

## Conclusion

The P3 milestone gate is met with machine-verified, upstream-backed evidence. Herdr remains the sole authority for terminal/pane/agent identity and state; the product adds only thin adapters and policy (digest-verified binary launch, fail-closed snapshot query, bounded read/wait/cancel, and an explicit fresh-run recovery choice). The P3 milestone is now **verified**.
