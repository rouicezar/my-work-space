# Herdr v0.8.2 Detach/Reclaim and Explicit Fresh-Run Recovery Verification (2026-09-02)

## Scope

This evidence closes P3-T15 for the provider-free scope only: it proves that a discarded Forma client can be replaced by a new client that reclaims the exact continuing Herdr terminal after a fresh `session.snapshot` plus `agent.get` reconciliation, that a stale reclaim claim fails closed, and that the product can offer an explicit fresh run with a distinct pane/terminal identity when no native provider-session reference exists.

It does **not** prove provider-native session resume. The repository's Codex fixture at `tests/fixtures/herdr_agent_bin/codex` never reports `agent_session`, and no `pane.report_agent_session` call, provider CLI, or `codex resume`/`claude --resume` invocation was exercised. Native resume remains unverified and unavailable until a separately approved real-provider probe proves upstream session continuity.

## What changed

- `forma_ai/herdr_adapter.py`:
  - Removed `resume_task()`. It previously accepted a caller-supplied `native_session_ref`, matched it against the live `agent_session` field, and then issued an unverified second `agent.start`, mislabeling the result `native_resume`. This mock-only path never validated against a real provider and is deleted rather than retained as a false capability.
  - Added `reclaim_task(*, task: HerdrTask) -> HerdrTask`. It performs `session.snapshot()` first, requires exactly one matching pane and one matching agent for the claimed pane ID, requires workspace/terminal/revision/normalized-state equality against the caller-held `HerdrTask`, then requires an `agent.get` refresh to match the same task exactly before restoring the new adapter instance's in-memory claim. Any mismatch (missing, duplicated, or drifted identity/revision/state) raises `ValueError` before any state is registered.
  - Added `start_fresh_task(*, previous_task, ...)`. It reuses the existing `spawn_task()` official `agent.start` detection path with the same product `task_id`, requires a different pane than `previous_task`, and requires the resulting run/pane/terminal identity to differ from the previous task, rejecting (and unregistering) an accidental identity collision.
  - Extracted `_task_state()` as a shared static helper so `reclaim_task()` and `_task_from_agent()` apply Herdr's `agent_status` → product-state mapping identically.
- `tests/test_herdr_adapter.py`: removed the mock-only native-resume success test; added focused tests for snapshot-then-`agent.get` reclamation, stale-revision rejection before any state mutation, and fresh-run pane/terminal isolation.
- `tests/test_herdr_integration.py`: extracted the P3-T12 live harness into a reusable `HerdrFixtureAgentIntegrationTestCase` (parameterized `PROOF_ID`, session/temp-dir prefixing, watchdog, server-log tail, cleanup) so `HerdrTwoFixtureAgentIntegrationTests` (P3-T12) and the new `HerdrDetachReconnectIntegrationTests` (P3-T15) are isolated by distinct `forma-p3t12-test-*` / `forma-p3t15-test-*` named sessions without weakening either proof.

## Live verification

Binary: pinned `herdr-macos-aarch64`, version `0.8.2`, protocol `20`, in an isolated named test session (`forma-p3t15-test-*`) with a deterministic fixture `PATH`/`HOME`.

Test: `tests.test_herdr_integration.HerdrDetachReconnectIntegrationTests.test_discarded_client_reclaims_then_starts_explicit_fresh_run`

Sequence proved live against the real server:

1. Client A opens a workspace/pane and launches the provider-free Codex fixture through official `agent.start`; the raw `agent_session` field is confirmed absent.
2. Client A's adapter and transport objects are discarded. The Herdr server process is asserted to remain alive (`self.server.poll() is None`); the server is never stopped, restarted, or handed off.
3. A new client B connects a fresh `HerdrSocketTransport`/`HerdrAdapter` to the same still-running named-session socket and calls `reclaim_task()` with only the task identity A held. `session.snapshot()` and `agent.get` both confirm the identical workspace/pane/terminal/revision/state before B's adapter accepts the claim.
4. B opens a real subscription (`HerdrSubscriptionListener`) on the reclaimed pane, prompts the continuing fixture into Herdr's officially detected `blocked` state, and receives that transition through the subscription — proving B is watching the same continuing agent, not a replacement.
5. Reusing the pre-transition task snapshot for `reclaim_task()` again is rejected with `ValueError` because the pane's revision/state has since moved; a stale claim cannot silently rebind.
6. B opens a distinct pane with an isolated working directory and calls `start_fresh_task()`. The result keeps the original product `task_id` but has a new run ID, pane ID, and terminal ID; a `fixture-b` command is confirmed running and completing only in that new terminal/cwd, with no blocked-fixture output leaking across panes.
7. Test duration: ~11.7 seconds live against the real server. Named-session cleanup (`session stop`, `session delete`) succeeded with no residue.

## Regression results

- `python3 -m unittest tests.test_herdr_adapter tests.test_herdr_presentation tests.test_herdr_integration -v`: 32 tests passed in 30.188s (includes the new P3-T15 live test and the retained P3-T12/P3-T13/P3-T14 live tests).
- `python3 -m unittest discover tests -v`: full Python suite passed.
- `swift test --package-path prototypes/packaging`: 43 tests passed with 2 environment-gated real-Keychain skips.
- No `forma-p3t12-*` or `forma-p3t15-*` named Herdr session directories remained after the run.

## Capability ledger correction

The ledger's prior "Resume after agent restart" row cited `HerdrAdapter.resume_task` and `pane.report_agent_session` as already reused. That citation is corrected: this evidence proves only client-side detach/reclaim plus an explicit fresh run against a provider-free fixture. Provider-native session resume through `pane.report_agent_session` and `codex resume`/`claude --resume` remains an open, separately gated probe requiring a real approved provider integration; it must not be cited as verified from this evidence or from the removed `resume_task()` method.

## Boundary preserved

- Herdr remains the sole authority for terminal/pane/agent identity, state, and revision. Forma's `HerdrTask` is only a caller-held identity claim reconciled against a fresh Herdr read; no recovery store, lifecycle journal entry, or persisted task-history state was introduced.
- No credentials, cloud/model calls, production/default Herdr sessions, or external network access were used; only disposable local named test sessions were created and fully cleaned up.
