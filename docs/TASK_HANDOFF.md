# Forma AI Task Handoff

## 2026-09-02 - P3-T15 - Qoder exit

Executor: Qoder agent
Scope verified: a discarded `HerdrAdapter` client's task is reclaimed by a fresh adapter instance only after a `session.snapshot()` and a subsequent `agent.get` both exactly match the caller-held claim's workspace/pane/terminal/revision/normalized-state; any mismatch (proven live with a stale-revision reclaim attempt) fails closed with no rebinding. The caller can then explicitly choose `start_fresh_task()`, which keeps the product `task_id` but requires and verifies a distinct run/pane/terminal identity in a live isolated named session; a real subsequent `blocked` transition on the reclaimed pane was observed via a fresh event subscription established only after reclamation.
Scope correction: native provider-session resume is NOT proven. The repository fixture never emits `agent_session`, so the previously existing `HerdrAdapter.resume_task()` was a mock-only fabrication (it accepted a caller-supplied `native_session_ref`, checked it locally, then issued an unproven second `agent.start` mislabeled `"native_resume"`). That method and its mock-only test were removed rather than kept as a false capability claim.
Files changed: `forma_ai/herdr_adapter.py` (added `reclaim_task()`, `start_fresh_task()`, shared `_task_state()`/`_task_from_agent()` helpers; removed `resume_task()`), `tests/test_herdr_adapter.py` (added reclaim/fresh-run unit tests, removed the native-resume mock test), `tests/test_herdr_integration.py` (extracted `HerdrFixtureAgentIntegrationTestCase` base class; added `HerdrDetachReconnectIntegrationTests` with the live P3-T15 proof), `evidence/upstream/herdr-v0.8.2-detach-fresh-run-recovery-verification-2026-09-02.md` (new), `docs/research/herdr-capability-ledger.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`, and their mandatory Chinese mirrors.
Verification: focused suite (`tests.test_herdr_adapter tests.test_herdr_presentation tests.test_herdr_integration`) passed 32 tests in 30.188s, including the new live P3-T15 test in 11.667s on first run with no corrections needed; full Python suite via `python3 -m unittest discover tests -v` passed with no failures; Swift package passed 43 tests with 2 environment-gated Keychain skips; no `forma-p3t15-*` named-session residue found; bilingual current-state parity and `git diff --check` passed.
Upstream decision: Herdr remains sole authority for terminal/pane/agent identity and state; reclamation and fresh-run are thin product-owned reconciliation and explicit-choice logic over `session.snapshot`/`agent.get`/`agent.start`, not a competing state machine. No persistent recovery store was added (deferred to P7-T02); native-provider-resume proof remains gated on a separately approved real-provider probe.
Commit and push: implementation/evidence commit `e562271` is pushed to `origin/main`; this documentation-sync update is the only remaining change.
Next exact action: commit and push this closeout synchronization, then begin P3-T16 (replace Preview agent cards with real Herdr runtime data).
Secret/external-write status: no credentials, cloud/model calls, production/default sessions, or external network; only disposable local named test sessions, self-cleaned.

## 2026-09-02 - P3-T15 - Qoder takeover

Executor: Qoder agent
Starting git state: `main` clean and synchronized with `origin/main` at `e7a6670`; P1-T09 correction `13c43d4` and its closeout `e7a6670` are pushed
Trigger: user explicitly authorized the push, requested a clean repository, and directed Qoder to claim P3-T15
Scope: prove official Herdr detach/reconnect and native or explicit fresh-run resume; revision/session reconciliation must pass and stale references must fail closed
Upstream search result: the Herdr v0.8.2 capability ledger names Herdr as the authority for terminal processes, session shape, detach/reattach, and supported native agent resume through `pane.report_agent_session`; reopening must reconstruct state from snapshot/events
Reusable entry point: pinned official Herdr binary and protocol 20 socket transport, `HerdrAdapter.resume_task`, snapshot/subscription presentation provider, existing revision/terminal identity safeguards, and disposable named-session integration harness
License obligation: Apache-2.0 external binary/socket reuse only; no upstream source, assets, names, or trademarks copied
Integration decision: reuse Herdr lifecycle and native resume where supported; product code may map authoritative state and offer an explicit fresh-run outcome but must not create a competing process/session state machine
Planned verification: recovery integration red test, official disposable-session probe, focused Herdr tests, Python and Swift suites, residue, bilingual parity, and `git diff --check`
Commit and push: this synchronized P3-T15 claim is committed and pushed before production changes
Next exact action: write the failing recovery integration contract before production changes
Secret/external-write status: no credentials, cloud/model calls, production/default sessions, or external network; only disposable local named sessions when tests begin

## 2026-09-02 - P1-T09 F5 correction - Qoder exit

Executor: Qoder agent
Scope: verified Codex's existing removal of obsolete `spawn_reported_task()` and its two dedicated unit tests; no other production/runtime behavior changed
Verification: production and test absence scans passed; focused Herdr suite passed 53 tests in 19.790s; full Python suite passed 296 tests with 1 expected skip in 23.986s; Swift package passed 43 tests with 2 environment-gated Keychain skips; no `forma-p3t*` named-session residue; bilingual current-state parity and `git diff --check` passed
Files changed: `forma_ai/herdr_adapter.py`, `tests/test_herdr_adapter.py`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`, and their mandatory Chinese mirrors
Upstream decision: Herdr `agent.start` remains the sole product task-launch authority; historical evidence may retain old terminology but production and test code contain no obsolete launcher reference
Commit and push: local commit `13c43d4` (`fix: remove obsolete Herdr reported-task launcher`) and synchronized closeout `e7a6670` are pushed to `origin/main`
Blocked items: none for P1-T09; P3-T15 is now separately in progress
Next exact action: execute P3-T15 recovery verification
Secret/external-write status: no credentials, cloud/model calls, production/default sessions, or external network; disposable local sessions self-cleaned

## 2026-09-02 - P1-T09 F5 correction - Qoder takeover

Executor: Qoder agent
Starting git state: `main` at `9c01a5a` with Codex's uncommitted four-file correction: the control-document claim plus deletion of `spawn_reported_task()` and its two dedicated unit tests
Trigger: user requested Qoder resume execution after reviewing Codex's takeover changes
Scope: verify only the existing precise removal; retain official `agent.start`, workspace/pane thin mappings, historical evidence, and current live integration proofs
Upstream search result: the recorded P3-T12 correction and F5 audit establish Herdr `agent.start` as the only selected task-launch authority; `pane.report_agent` remains an upstream reporting hook, not a product task launcher
Reusable entry point: existing `HerdrAdapter.spawn_task`, Herdr focused/full test suites, Swift package tests, and disposable named-session test framework
License obligation: Apache-2.0 external Herdr binary/socket reuse only; no upstream source, assets, names, or trademarks copied
Integration decision: remove the superseded client-reported launcher rather than retain two launch authorities; runtime state remains Herdr-authoritative
Planned verification: production/test absence scan, Herdr focused suite, full Python suite, Swift package, named-session residue, bilingual parity, and `git diff --check`
Commit and push: pending explicit user authorization
Next exact action: run the scoped verification suite and record its results in both language sets
Secret/external-write status: no credentials, cloud/model calls, production/default sessions, or external network

## 2026-09-02 - P1-T09 F5 correction - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `9c01a5a`
Trigger: user accepted the exact recommendation to remove `spawn_reported_task()` and its two obsolete unit tests, verify, commit/push, then enter P3-T15
Scope: delete only the duplicate production adapter method and the two tests that exist solely for it; retain official `agent.start`, workspace/pane thin mappings, historical evidence, and all current live integration proofs
Upstream decision: Herdr `agent.start` is the sole selected task-launch authority; `pane.report_agent` remains an upstream reporting hook but is no longer wrapped as a product task launcher
Planned verification: absence scan, Herdr focused suite, full Python suite, Swift package, named-session residue, bilingual parity, and `git diff --check`
Commit and push: pending
Next exact action: remove the method and the two exact unit-test methods
Secret/external-write status: no credentials, cloud/model calls, production/default sessions, or external network

## 2026-09-02 - P3-T12 diagnostic hardening - exit

Executor: Codex root agent
Scope: make the live P3-T12 proof bounded and observable without changing Herdr product behavior, then audit Qoder's P3 runtime additions for upstream duplication
Actions: added flushed elapsed-time stages, captured server output with failure tail, consistent 15s request/10s marker/5s Agent-start/10s cleanup bounds, a 45s whole-test watchdog, and cleanup return-code enforcement
Verification: initial live pass 10.174s; 10 consecutive live passes completed 10/10 in 100.312s; focused Herdr 55 passed in 19.620s; full Python 298 passed with 1 expected skip in 23.849s; Swift 43 passed with 2 environment-gated skips; `git diff --check` passed; no P3-T12/T13/T14 named-session residue
Evidence: `evidence/upstream/herdr-v0.8.2-p3t12-test-diagnostics-2026-09-02.md`
Duplication audit: transport, snapshot/subscription presentation, bounded read/wait, and two-stage cancellation remain thin upstream mappings or justified product UI/approval policy. One concrete suspect exists: `spawn_reported_task()` is an obsolete production adapter method used only by two unit tests after live P3-T12 switched to official `agent.start`; the audit records it as F5 and blocks P3-T15 until removal or new retention evidence.
Commit and push: diagnostic/evidence/audit commit `45aaa16` (`test: bound herdr fixture diagnostics`) is pushed to `origin/main`; this exact push-state line is recorded by the following metadata commit
Blocked items: P3-T12 diagnostics have no blocker; P3-T15 is held at the upstream-first F5 decision checkpoint
Next exact action: commit and push this diagnostic/audit batch, then obtain direction to remove `spawn_reported_task()` and its obsolete tests or supply a justified retained use
Secret/external-write status: no credentials, cloud/model calls, production/default Herdr sessions, or external network; disposable local sessions only

## 2026-09-02 - P3-T12 diagnostic hardening - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `95f73a4`; P3-T14 is independently reviewed, verified, committed, and pushed
Trigger: user approved the ordered correction plan and specifically required fixing P3-T12's silent long-wait behavior before P3-T15
Requirements: preserve the existing real Herdr lifecycle proof; expose bounded progress for server, panes, agent detection, parallel marker, cancel, and cleanup; retain a useful server-log tail on failure; cap the whole test; prove cleanup; run ten consecutive live passes
Design: change only the integration-test harness, not Herdr product logic; use flushed stage diagnostics, consistent short protocol timeouts, a main-thread watchdog, captured server output, and exact cleanup reporting
Planned verification: diagnostic unit/static checks where useful, ten consecutive P3-T12 live runs, focused Herdr suite, full Python, Swift package, residue check, bilingual parity, and `git diff --check`
Commit and push: pending
Next exact action: implement bounded stage/log/watchdog support in `tests/test_herdr_integration.py`
Secret/external-write status: no credentials, cloud/model calls, production/default sessions, or external network; disposable local Herdr sessions only

## 2026-09-02 - P3-T14 - independent review exit

Executor: Codex root agent
Scope: independently review Qoder's uncommitted P3-T14 batch, repair the missing Chinese handoff mirror, close cancellation-safety findings, and reverify the full batch
Findings corrected: `task_status()` could silently rebind a claimed run to a replacement terminal in the same pane, defeating later cancellation identity checks; confirmed force close left stale run-to-task and run-to-pane registries; foreground-process ordering could create unstable equality checks
Actions: fail closed on refreshed workspace/pane/terminal replacement; normalize foreground process ids; remove every run registry after confirmed force close; add replacement-terminal and post-close invalidation regression coverage; expand the evidence boundary so the fixture is not presented as a real model loop
Verification: targeted regressions 2 passed; focused Herdr suite 55 passed in 19.705s; full Python 298 passed with 1 expected skip in 24.352s; Swift package 43 passed with 2 environment-gated Keychain skips; `git diff --check` passed. A stopped historical P3-T13 test-session directory was found and deleted through the exact Herdr session command; no P3-T12/T13/T14 named-session residue remains.
Files changed: Qoder's P3-T14 adapter/tests/fixture/ledger/evidence/control batch plus independent-review corrections in the adapter, tests, evidence, and four controls
Commit and push: pending immediately after this synchronized exit record
Blocked items: none for P3-T14; P3-T12 test diagnostics still require a separate correction before P3-T15, and the fixture remains lifecycle evidence rather than a real model-Agent proof
Next exact action: commit and push this verified batch, then claim the P3-T12 diagnostic-hardening correction
Secret/external-write status: no credentials, cloud/model calls, production/default Herdr sessions, or destructive broad operations; one exact stopped test session was deleted

## 2026-09-02 - P3-T14 - independent review takeover

Executor: Codex root agent
Starting git state: `main` and `origin/main` at `21884e7` with Qoder's uncommitted P3-T14 batch; the Chinese handoff exit mirror was missing
Trigger: user approved the six-step correction sequence beginning with mirror repair, independent diff review, and P3-T12 diagnostic hardening
Scope: repair the P3-T14 mirror, independently review every uncommitted P3-T14 change, fix all commit-blocking findings, verify, commit, and push before any P3-T15 claim
Review finding: `task_status()` refreshed and overwrote a claimed run without rejecting workspace/pane/terminal replacement, so a later cancel could target a replacement Agent in a reused pane; force close also left stale run-to-task and run-to-pane registry entries
Correction: fail closed when refreshed workspace, pane, or terminal identity differs; normalize process IDs for stable reconciliation; remove every run registry after confirmed force close; add regression coverage
Planned verification: targeted regression tests, full Herdr focused suite, full Python suite, full Swift package, repeated live P3-T12 proof, bilingual parity, and `git diff --check`
Commit and push: pending
Next exact action: run focused verification, finish evidence/control corrections, then run full verification before committing
Secret/external-write status: no credentials, cloud/model calls, production/default Herdr sessions, or destructive operations; only disposable local Herdr test sessions

## 2026-09-02 - P3-T14 - Qoder exit

Executor: Qoder agent
Scope: official Herdr v0.8.2 wait, real blocked state, bounded ANSI-stripped output read, revision/identity-checked graceful interrupt, and explicit force-close escalation
Actions: added task-level `agent.wait`, bounded `agent.read`, and `pane.process_info` mappings; retained Herdr terminal identity with the claimed task; required current revision, terminal identity, and foreground-process reconciliation before `ctrl+c`; required a matching graceful claim, `force_confirmed=true`, fresh identical reconciliation, `pane.close`, and post-close `agent_not_found` before reporting a force close. Added a provider-free blocked fixture and live acceptance test.
Upstream evidence: the bundled schema and disposable named-session probes established that `agent.wait` returns `agent_info`, `agent.read` returns `pane_read`, unmatched status is a `timeout`, and `pane.close` is confirmed by `agent_not_found`. The real blocked path uses the official Codex detector's `osc_title_blocked` rule, not client-reported state.
Verification: new lifecycle unit tests 3 passed; Herdr adapter tests 26 passed; live Herdr integration tests 3 passed; full Python suite 297 passed with 1 expected skip; Swift package 43 passed with 2 environment-gated Keychain skips; `git diff --check` passed; no `forma-p3t14-*` named-session residue remained.
Evidence: `evidence/upstream/herdr-v0.8.2-lifecycle-read-cancel-verification-2026-09-02.md`; ledger updated at `docs/research/herdr-capability-ledger.md`.
Files changed: `forma_ai/herdr_adapter.py`, `tests/test_herdr_adapter.py`, `tests/test_herdr_integration.py`, `tests/fixtures/herdr_agent_bin/codex`, Herdr ledger/evidence, both English controls, and the Chinese progress mirror.
Commit and push: not requested; no commit or push was performed.
Blocked items: P3-T14 implementation has no blocker, but the Chinese handoff exit mirror at `/Users/rouice/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyNote/00_资源库/11_项目开发/Forma AI/Forma AI-任务交接-中文.md` was not written because the external iCloud-vault permission classifier blocked the edit. Catch-up: after authorization, prepend the equivalent P3-T14 Qoder exit record from this entry before starting product work, committing, or claiming P3-T15. Provider-native resume/detach remain P3-T15; runtime-card replacement remains P3-T16.
Next exact action: obtain the Chinese handoff mirror write authorization and apply that catch-up, then request a commit decision for this verified batch; once authorized, commit it and then claim P3-T15 for detach/reconnect and native or explicitly fresh-run resume.
Secret/external-write status: no credentials, cloud/model calls, production/default Herdr session, external network request, or persistent user configuration change; only automatically cleaned disposable local sessions and temporary fixtures.

## 2026-09-02 - P3-T14 - Qoder takeover

Executor: Qoder agent
Starting git state: `main` has Codex's uncommitted P3-T14 control-document claim; no runtime code or test change is present
Trigger: user requested that Qoder resume after inspecting the Codex takeover changes
Scope: prove real wait, blocked, bounded artifact/output read, revision-checked graceful cancel, and explicit force-cancel escalation through official Herdr v0.8.2 surfaces
Upstream search result: the Codex checkpoint records bundled protocol-20 schema entries for `agent.wait(target, timeout_ms, until)`, `agent.read(target, source, lines, format, strip_ansi)`, `pane.read`, `pane.process_info`, `pane.send_keys`, and `pane.close`; Qoder must probe live response/state semantics before implementation
Reusable entry point: pinned Herdr binary/socket transport, existing run/pane/revision registry, provider-free official `agent.start` fixture, and isolated named-session test harness
License obligation: Apache-2.0 external binary/socket reuse only; no upstream source, assets, names, or trademarks copied
Integration decision: Herdr remains lifecycle/output authority; Forma adds only bounded-read and cancellation policy. Graceful interrupt requires matching claimed revision; force close requires a second explicit escalation plus fresh pane/agent reconciliation and fails closed on stale identity
Planned verification: schema/live probe; red unit tests; live blocked/wait/bounded-read/graceful/force proof; focused and full Python; bilingual parity; `git diff --check`
Commit and push: pending
Next exact action: probe real `agent.wait`/`agent.read`/`pane.process_info`/`pane.close` response and error semantics in a disposable named session
Secret/external-write status: no credentials, cloud/model calls, production sessions, or default Herdr session; disposable local named sessions only

## 2026-09-02 - P3-T14 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `21884e7`
Trigger: user explicitly authorized P3-T14 and deferred manual testing until P3-T14～T16 plus the local-Qwen loop are complete
Scope: prove real wait, blocked, bounded artifact/output read, revision-checked graceful cancel, and explicit force-cancel escalation through official Herdr v0.8.2 surfaces
Upstream search result: bundled protocol-20 schema confirms `agent.wait(target, timeout_ms, until)`, `agent.read(target, source, lines, format, strip_ansi)`, `pane.read`, `pane.process_info`, `pane.send_keys`, and `pane.close`; live response/state details still require a disposable-session probe before implementation
Reusable entry point: pinned Herdr binary/socket transport, existing run/pane/revision registry, provider-free official `agent.start` fixture, and isolated named-session test harness
License obligation: Apache-2.0 external binary/socket reuse only; no upstream source, assets, names, or trademarks copied
Integration decision: Herdr remains lifecycle/output authority; Forma adds only bounded-read and cancellation policy. Graceful interrupt requires matching claimed revision; force close requires a second explicit escalation plus fresh pane/agent reconciliation and fails closed on stale identity
Planned verification: schema/live probe; red unit tests; live blocked/wait/bounded-read/graceful/force proof; focused and full Python; bilingual parity; `git diff --check`
Commit and push: pending
Next exact action: probe real `agent.wait`/`agent.read`/`pane.process_info`/`pane.close` response and error semantics in a disposable named session
Secret/external-write status: no credentials, cloud/model calls, production sessions, or default Herdr session; disposable local named sessions only

## 2026-09-02 - P3-T13 - exit

Executor: Codex root agent
Scope: bind Herdr snapshot and non-replaying event delivery to a fail-closed Python/Swift runtime presentation provider and prove real forced socket-loss recovery
Actions: added `HerdrPresentationProvider`; rejected stale revisioned deltas; reconciled revisionless live events through authoritative snapshots; invalidated old agents to `unknown` before reconnect; proved server restart removes old pane identity and fresh snapshot/new subscription resume on a new pane; added `herdr-snapshot` Supervisor envelope and Swift `RuntimePresentationProvider`; recorded evidence and closed the ledger gap
Red/correction evidence: provider import initially failed; live restart then exposed an empty snapshot instead of old-pane recovery; the next live failure exposed that v0.8.2 subscription status events omit revision, leading to snapshot reconciliation rather than fabricated ordering
Verification: 50 focused Python tests passed in 4.433s; full Python 293 passed with 1 expected skip in 18.892s; full Swift 43 passed with 2 environment-gated skips in 9.484s; `git diff --check` clean
Evidence: `evidence/upstream/herdr-v0.8.2-presentation-reconnect-verification-2026-09-02.md`
Files changed: Python presentation provider, live/unit tests, Supervisor command/tests, Swift protocol/provider/tests, Herdr ledger/evidence, and four bilingual controls
Commit and push: implementation/evidence `0c437f6` (`feat: bind herdr presentation recovery`) and closeout `28a9215` (`docs: close herdr presentation recovery`) pushed to `origin/main`; this exact push-state line follows in the terminal metadata sync
Blocked items: none for P3-T13; real wait/blocked/artifact/cancel is P3-T14, detach/native recovery P3-T15, and runtime card replacement P3-T16
Next exact action: after the executing-plans checkpoint claim P3-T14 and write real wait/blocked/bounded-artifact/graceful-and-force-cancel acceptance tests
Secret/external-write status: no credentials, cloud/model calls, production sessions, or default Herdr session; disposable local named sessions only

## 2026-09-02 - P3-T13 - Codex resume takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `06b26df`
Trigger: user approved the real-closure sequence and required the next manual build to accept a real task, involve local Qwen, start at least two Herdr agents, show live state, and cancel one task; no further shell beautification is authorized before that gate
Scope: finish Qoder's committed P3-T13 slice by proving forced listener loss, immediate stale/unknown state, authoritative snapshot reconciliation, revision/sequence rejection, automatic resubscription, resumed live delivery, then bind the Supervisor envelope and Swift runtime presentation provider
Upstream search result: Herdr v0.8.2 remains the runtime authority; its verified snapshot-first and non-replaying subscription semantics require product-owned lifecycle orchestration only, not a second state store
Reusable entry point: existing `HerdrSubscriptionListener`, `HerdrAdapter.snapshot()`/`wait_for_event()`, official socket API, SupervisorProtocol bridge, and Swift presentation contract
License obligation: Apache-2.0 external binary/socket reuse; no upstream source, assets, names, or trademarks copied
Integration decision: on listener failure, invalidate displayed runtime truth before reconnect; recover only by fresh snapshot reconciliation before opening a new subscription; reject stale deltas by authoritative revision/sequence; runtime UI never falls back to preview cards
Planned verification: failing forced-loss test first; focused transport/adapter/provider tests; live named-session reconnect proof; Supervisor and Swift mapping tests; full Python and Swift suites; bilingual parity; `git diff --check`
Commit and push: pending
Next exact action: write the forced socket-loss red test and the presentation-provider state contract
Secret/external-write status: no credentials, cloud calls, or production sessions; disposable local Herdr sessions only

## 2026-09-02 - P3-T12 acceptance correction - exit

Executor: Codex root agent
Scope: correct P3-T12 from a client-reported shell proof to two agents actually launched and detected through official Herdr `agent.start`
Actions: withdrew the old real-agent and shell-cancel claims in the evidence/ledger; replaced the shell-only live test with a provider-free executable fixture reached through an isolated temporary HOME/PATH; added schema `timeout_ms`; made `spawn_task` reject malformed or still-pending launches and wait for Herdr-detected idle plus `agent.get` refresh; required distinct run/pane/terminal/name identities, `agent=codex`, `interactive_ready=true`, parallel completion, pane-exact graceful cancellation, no leak artifact, and no cross-pane output; converted both live test classes to `TemporaryDirectory`
Red evidence: with no safe fixture, approval review correctly blocked any possible fallback to the real Codex CLI; after PATH isolation the live test showed socket `agent.start` returning `agent_started` with `launch_pending=true`, proving the adapter's false-running defect; the deterministic fixture then drove the new wait-and-refresh path green
Verification: corrected live test passed in 10.13s; 49 Herdr transport/adapter/integration tests passed in 13.60s; full Python suite passed 291 tests with 1 expected opt-in Semantica skip in 17.74s; `git diff --check` clean; named-session residue empty
Evidence: `evidence/upstream/herdr-v0.8.2-two-fixture-agent-isolation-verification-2026-09-01.md` correction section and corrected P3-T12 ledger entry
Files changed: Herdr adapter; adapter/integration tests; provider-free executable fixture; evidence and Herdr ledger; both English controls and both mandatory Chinese mirrors
Model-routing decision from user follow-up: prefer the already deployed Qwen3-0.6B-4bit through the verified local oMLX path when a real model is needed; adapt DeepSeek in P5, but every real cloud run still requires exact outgoing payload, privacy scope, model/token/cost estimate, and per-run explicit approval
Commit and push: implementation/evidence `bc860f2` (`fix: prove real herdr fixture agents`) and closeout synchronization `44e6f0a` (`docs: close herdr agent acceptance correction`) pushed to `origin/main`; this final push-state line follows in the terminal metadata sync
Blocked items: none for P3-T12; provider-native session resume remains P3-T15, and the fixture deliberately proves Herdr lifecycle without cloud execution
Next exact action: commit/push this verified correction batch; after the executing-plans review checkpoint claim P3-T13 and add a forced socket-loss/stale-state/snapshot-reconciliation/resubscribe red test before Supervisor/Swift binding
Secret/external-write status: no credentials, cloud calls, model calls, downloads, or production sessions; only disposable local Herdr test sessions

## 2026-09-02 - P3-T12 acceptance correction - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `faf4811`
Trigger: user approved the independent audit's correction order and asked Codex to take over continued execution until the product runs
Scope: withdraw the overbroad P3-T12 real-agent acceptance, preserve its valid pane-isolation evidence, replace shell-dependent and leaking fixtures with deterministic self-cleaning fixtures, and prove two agents actually launched and detected through Herdr `agent.start`; P3-T13 committed work is preserved and temporarily returned to pending
Current verification fact: P3-T12 passed in 4.79s; all 48 Herdr-module tests passed in 8.00s; full Python suite passed 290 tests with 1 expected opt-in Semantica skip in 11.98s; the prior 62-second zsh blocker is not currently reproducible and is no longer current-state truth
Acceptance correction: `pane.send_text` plus client-owned `pane.report_agent` proves pane execution/isolation but cannot satisfy a real-agent gate; the P3-T13 test currently proves a normal second subscription after `stop()`, not forced socket-loss recovery or automatic reconciliation
Upstream search result: official Herdr v0.8.2 `agent.start` is the existing upstream entry point and reports success only after a supported interactive agent is detected and ready in the target pane; no product-owned agent launcher will be created
Reusable entry point: verified Herdr binary/socket transport, `HerdrAdapter.spawn_task` 1:1 over `agent.start`, unique named sessions, and repository-local fixture seams
License obligation: Apache-2.0 external binary/socket reuse only; no upstream source, assets, names, or trademarks are copied
Integration decision: P3-T12 stays the sole `in_progress` task; P3-T13 returns to `pending` without reverting commit `faf4811`; no cloud-backed Codex/Qoder/Claude session may be launched silently, so the correction must use a local deterministic supported-agent fixture or stop for explicit approval if Herdr cannot detect one without a real provider
Planned verification: expected red real-agent acceptance test; deterministic shell/fixture readiness without user dotfiles; automatic temporary-directory and named-session cleanup on pass/failure; two `agent.start` results with distinct native agent/session identities; parallel work, cancellation and cross-pane isolation; focused Herdr tests; full Python suite; `git diff --check`; bilingual control parity
Commit and push: pending
Next exact action: write the failing acceptance contract that rejects `pane.report_agent`-only fixtures, then inspect Herdr's supported-agent detection seam for a provider-free local fixture
Secret/external-write status: no credentials, cloud calls, downloads, or production sessions; local disposable Herdr sessions only

## 2026-09-01 - P3-T13 - takeover

Executor: Qoder agent
Starting git state: `main` clean and synchronized with `origin/main` at `ae81338`
Trigger: user authorization on 2026-09-01 ("继续执行 P3-T13") continuing the standing relay-priority authorization ("优先推进 P3-T10～T15……固定 Herdr artifact，接官方 transport，完成真实双 Agent、事件订阅、取消、重连与恢复"); P3-T13 claimed per the next exact action recorded identically in all four control documents; plan goals, requirements, and audit logic unchanged; P4-T14 remains pending as the default next frontend task
Scope: bind snapshot and event subscriptions (`events.subscribe`/`events.wait`) to the workbench presentation provider, with a reconnect/resubscribe test proving no stale UI after socket loss and live state-transition evidence; acceptance is that the UI cannot override Herdr semantic state
Upstream search result: the bundled API schema (protocol 20, 91 request methods) plus a live probe against the pinned v0.8.2 binary in disposable named sessions (`forma-p3t13-probe-<uuid8>`) established the delivery model. Schema: `events.subscribe` takes `{subscriptions: [Subscription]}` with 27 dotted subscription types (extras required: `pane.output_matched` type+pane_id+source+match, `pane.agent_status_changed` type+pane_id, `pane.scroll_changed` type+pane_id) and returns `{type: "subscription_started"}`; `events.wait` takes `{match_event: EventMatch, timeout_ms: nullable uint64}` with underscore EventMatch forms (e.g. `pane_agent_status_changed` requires event+pane_id+agent_status) and returns `{type: "wait_matched", event: EventEnvelope}` on match; `session.snapshot` returns the full SessionSnapshot (required workspaces/tabs/panes/layouts/agents, optional focused ids; AgentInfo requires agent_status/focused/pane_id/revision/tab_id/terminal_id/workspace_id). Live probe facts: (1) request connections are closed by the server immediately after the response — one request per connection, including `events.wait` (EOF right after `wait_matched`); (2) subscription connections are the exception: a dedicated subscriber socket stays open past the `subscription_started` ack and pushes event envelopes `{"event": <dotted>, "data": {...}}` indefinitely, surviving 12s+ idle; (3) subscribing to `workspace.created` replays the existing workspaces as initial state (full WorkspaceInfo payloads), but `pane.agent_status_changed` does NOT replay current agent state — so the presentation flow must be snapshot-first, then subscribe for live deltas; (4) a second `events.subscribe` on the same socket kills the connection (one subscription per dedicated connection); (5) events fired while disconnected are NOT replayed to a later subscriber, but a fresh connection can resubscribe immediately and receive subsequent events — reconnect must therefore resubscribe AND take a fresh snapshot to avoid stale UI; (6) `events.wait` timeout returns an error `{"code": "timeout", "message": "timed out waiting for event match"}` and `timeout_ms: null` blocks until match; (7) `events.wait` envelopes use the underscore event name while subscribe deliveries use the dotted form
Reusable entry point: `HerdrSocketTransport` (validated P3-T11) for one-shot requests (`session.snapshot`, `events.wait`), a new dedicated long-lived connection capability in `forma_ai/herdr_transport.py` for `events.subscribe` delivery, the existing `Request` seam in `forma_ai/herdr_adapter.py`, the presentation contract `docs/contracts/product-preview-presentation.md` §7 (RuntimePresentationProvider maps authoritative adapter responses; preview and runtime never mix), the SupervisorProtocol envelope bridge (`scripts/supervisor.py` ↔ `prototypes/packaging/Sources/SupervisorProtocol/`), the verified aarch64 binary, and disposable uniquely named test sessions
License obligation: the Apache-2.0 Herdr binary runs as an external process driven through its documented socket API; no upstream source, names, or assets are copied into product code; the adapter implements only the schema-derived wire contract
Integration decision: reuse Herdr's own delivery semantics — the product adds (a) a thin `snapshot()` adapter method 1:1 over `session.snapshot` returning Herdr-authoritative workspaces/tabs/panes/agents, (b) a thin event-subscription capability 1:1 over `events.subscribe` on a dedicated long-lived connection (per the probe: one subscription per connection), surfaced to the presentation layer so UI state is a pure mapping of Herdr state, and (c) a thin `wait_for_event` 1:1 over `events.wait` where a one-shot blocking wait fits better than a listener; after socket loss the product reconnects by design as fresh snapshot → resubscribe → reconcile (never trusting pre-loss UI state), which the reconnect test must prove; runtime state stays with Herdr, the product saves only correlation metadata; no product-owned runtime substitute is introduced
Planned verification: red/green unit tests over the scripted fake `Request`/socket seam for snapshot mapping and subscription lifecycle (ack validation, event envelope handling, EOF/close surfacing); live integration test in a uniquely named session proving live state transitions (working → idle via subscription) and reconnect/resubscribe correctness (socket loss → missed events not replayed → fresh snapshot reconciles, no stale UI); supervisor envelope command for snapshot/event payloads with Swift-side protocol mapping tests; full Python suite `python3 -m unittest discover tests`; `swift test --package-path prototypes/packaging`; `git diff --check`; evidence file under `evidence/upstream/`; Herdr ledger update; both English controls and both Chinese mirrors updated in the same closeout
Commit and push: pending
Next exact action: write the failing adapter/transport tests for the subscription listener and snapshot method, then implement `forma_ai/herdr_transport.py` subscription support and the `forma_ai/herdr_adapter.py` methods
Secret/external-write status: no credentials, no cloud model calls, no external network access; live probes and tests run local headless Herdr servers only, each in a uniquely named session under `~/.config/herdr/sessions/` created, verified, stopped, and deleted by the probe/test itself; the default session is never started or contacted

## 2026-09-02 - P3-T13 - interim progress (user-requested stage commit)

Executor: Qoder agent
Trigger: user interrupt ("我强行打断你，现在阶段性总结一次，把仓库中的修改提交，让仓库干净") — stage summary plus a commit leaving the repository clean; P3-T13 stays `in_progress`, plan goals, requirements, and audit logic unchanged
Completed since takeover: (a) `HerdrSubscriptionListener` in `forma_ai/herdr_transport.py` — one dedicated long-lived connection per `events.subscribe` (per probe fact 4), ack validation (`subscription_started`, error → `HerdrRequestError`, malformed → `HerdrProtocolError`/`HerdrTransportError`), newline-delimited event loop with a persistent read buffer (a single `recv` may coalesce ack + events), cross-thread `stop()` closing the socket; (b) `snapshot()` and `wait_for_event()` thin adapter methods over `session.snapshot`/`events.wait` with response-type validation and dataclass mapping; (c) unit tests over the scripted fake seams (transport 12, adapter snapshot/wait classes) and the live test `HerdrEventSubscriptionIntegrationTests.test_live_transitions_subscription_and_reconnect_resubscribe` proving the full chain: snapshot-first (protocol 20, `working`), live subscription delivering the `blocked` transition, `events.wait` current-state match + deterministic `timeout` error on a never-set state, post-reconnect resubscribe delivering `working`
New upstream semantics discovered (correction to takeover fact 5, to be folded into the evidence file at closeout): `events.wait` matches the pane's **current state**, not an event history — a state set at any past time (observed up to 6s) matches immediately even with no subscription attached; a superseded state never matches; the non-replay finding stands for the subscription path (a just-fired-and-superseded event does not match a later wait). The original live-test design wrongly assumed non-replay applied to `events.wait`; the test was corrected to assert the actual semantics (current-state match positive, never-set `unknown` → `timeout` negative)
Environment drift discovered (pre-existing, not a P3-T13 regression): this machine's `/bin/zsh -i` interactive startup now takes ~62s (5% CPU; the pane shell inherits the Herdr server's `$SHELL`), so `tests/test_herdr_integration.py::HerdrTwoFixtureAgentIntegrationTests` fails at HEAD on this machine (`pane.wait_for_output` 20s marker timeout; the P3-T12 suite was green at commit time on a fast shell). A probe confirmed Herdr panes follow the server process `$SHELL` and that pinning `SHELL=/bin/sh` makes panes ready in ~1s — but POSIX sh continues executing the remainder of a command line after SIGINT, which would turn the P3-T12 no-leak assertion into a deterministic failure; the `SHELL` pins were therefore reverted and the SIGINT-per-shell probe (`/bin/bash` candidate, expected to combine fast startup with interactive SIGINT aborting the pending line) was interrupted by the user's stage-commit request and not run
Verification evidence: `python3 -m unittest tests.test_herdr_integration.HerdrEventSubscriptionIntegrationTests tests.test_herdr_adapter tests.test_herdr_transport` → 47 tests OK (3.4s), including the live subscription test; `git diff` since `63d34af` for `forma_ai/herdr_transport.py`/`herdr_adapter.py` is purely additive (new classes/methods; the request path is byte-identical), so the P3-T12 live-test failure is environmental, not caused by P3-T13 changes; full-suite state on this machine right now: 290 tests, 1 failure (the P3-T12 live test, environmental, fails identically at HEAD), 1 skipped (expected)
Files changed: `forma_ai/herdr_transport.py`, `forma_ai/herdr_adapter.py`, `tests/test_herdr_transport.py`, `tests/test_herdr_adapter.py`, `tests/test_herdr_integration.py`, both English controls, and both mandatory Chinese mirrors (outside the repository)
Commit and push: this interim commit records the verified subscription/snapshot/wait work together with the interim-state control documents; P3-T13 remains open
Blocked items: P3-T12 live test on this machine is blocked by the slow interactive zsh startup (environment, not product code); recovery action: after this stage commit, run the SIGINT-per-shell probe (candidate `/bin/bash`) and pin the test-server `SHELL` to a fast shell whose interactive SIGINT aborts the pending command line, or fix the local zsh startup configuration
Next exact action: resume P3-T13 — resolve the P3-T12 test-shell pin via the SIGINT probe, then add the supervisor envelope command (`scripts/supervisor.py`) and the Swift-side `RuntimePresentationProvider` + `SupervisorProtocol` payload mapping with tests, then full closeout (evidence file including the `events.wait` semantics correction, Herdr ledger update, bilingual exit entries, two-commit pattern, push)

## 2026-09-01 - P3-T12 - exit

Executor: Qoder agent
Scope: run two real isolated fixture agents through Herdr using only schema-documented methods (never `pane.run`) — parallel execution, two distinct panes/runs, and no input, state, artifact, or cancel leakage — via three thin adapter methods over `workspace.create`, `pane.split`, and `pane.report_agent`
Actions: implemented `open_workspace`, `open_pane`, and `spawn_reported_task` in `forma_ai/herdr_adapter.py` (each 1:1 over a schema method with response-type validation; `spawn_reported_task` drives `pane.send_text` → `pane.report_agent` (`source: "forma-fixture"`, `state: "working"`) → `agent.get`, returns a `HerdrTask` with run_id `herdr:<task_id>:<pane_id>` registered in all three run-id registries so fixture tasks reuse the existing `task_status`/`cancel_task` lifecycle unchanged; `correlation_id` stays product-side metadata); added 5 unit tests (`HerdrAdapterFixtureTests` in `tests/test_herdr_adapter.py`) pinning exact params, call sequences, response validation, and registry behavior; added the live proof `tests/test_herdr_integration.py` — unique named session `forma-p3t12-test-<uuid8>` (headless server, self stop/self delete, default session never contacted), two distinct panes with distinct temp cwds, parallelism proven by timing (agent B finished inside agent A's 8s sleep window: `b_end - a_start < 8`), real Herdr state via `agent.get`/`session.snapshot` (`working` while running, both `idle` at close on distinct panes), pane-exact graceful cancel (A's `ctrl+c` interrupted its sleep; post-sleep leak steps never executed), and isolation proven across artifacts (`a_leak.txt` absent; dir_a exactly `a_start.txt`; dir_b exactly `b_start.txt`+`b_end.txt`), input, and pane text (no cross-pane markers; executed-output markers checked as timestamp regexes because pane text contains the echoed command verbatim); wrote `evidence/upstream/herdr-v0.8.2-two-fixture-agent-isolation-verification-2026-09-01.md`; updated the Herdr ledger (header, P3-T12 gap CLOSED with evidence pointer, remaining gap narrowed to P3-T13+ event subscription/presentation binding/wait-blocked-artifacts/detach-reconnect-recovery, and the P3-T10 `pane.split` wording corrected — it creates an empty pane with no command field, per live probing)
Verification evidence: red state confirmed first — the 6 new tests failed with `AttributeError: 'HerdrAdapter' object has no attribute 'open_workspace'/'open_pane'/'spawn_reported_task'` (correct missing-method red); after implementation `python3 -m unittest tests.test_herdr_adapter -v` → 16 tests OK (5 new); one intermediate live-test failure was an over-strict assertion matching the echoed input line rather than a product bug — corrected to timestamp-regex matching of executed output only, then `python3 -m unittest tests.test_herdr_integration -v` → 1 live test OK (4.7s); full suite `python3 -m unittest discover tests` → 277 tests, OK, 1 skipped (expected real-Semantica integration test), up from 271 with exactly the 6 new tests; post-run residue check `~/.config/herdr/sessions/` empty and the default-session socket never created; `git diff --check` clean
Files changed: `forma_ai/herdr_adapter.py`, `tests/test_herdr_adapter.py`, `tests/test_herdr_integration.py` (new), `docs/research/herdr-capability-ledger.md`, `evidence/upstream/herdr-v0.8.2-two-fixture-agent-isolation-verification-2026-09-01.md` (new), both English controls, and both mandatory Chinese mirrors (outside the repository)
Commit and push: implementation/evidence commit `63d34af` (`feat: run two isolated fixture agents through herdr`) includes the takeover-state control documents; this exact closeout metadata follows in the synchronization commit; both pushed to `origin/main`
Blocked items: none
Next exact action: claim P3-T13 — bind snapshot and event subscriptions (`events.subscribe`/`events.wait`) to the workbench presentation provider with a reconnect/resubscribe test proving no stale UI after socket loss and live state-transition evidence; P4-T14 remains the default next frontend task
Secret/external-write status: no credentials, no cloud model calls, no external network access; one local headless Herdr test server per live test run in a uniquely named session under `~/.config/herdr/sessions/`, created, verified, stopped, and deleted by the test itself; the default session was never started or contacted; fixture artifacts live only in disposable per-test temp directories

## 2026-09-01 - P3-T12 - takeover

Executor: Qoder agent
Starting git state: `main` clean and synchronized with `origin/main` at `cf0a898`
Trigger: user authorization on 2026-09-01 ("很好，执行下一步动作") continuing the standing relay-priority authorization ("优先推进 P3-T10～T15……完成真实双 Agent、事件订阅、取消、重连与恢复"); P3-T12 claimed per the next exact action recorded identically in all four control documents; plan goals, requirements, and audit logic unchanged; P4-T14 remains pending as the default next frontend task
Scope: run two real isolated fixture agents through Herdr using only schema-documented methods (never `pane.run`) with parallel execution, two distinct panes/runs, and no input, state, artifact, or cancel leakage
Upstream search result: the bundled API schema (protocol 20, 91 request methods) plus an empirical probe against the pinned v0.8.2 binary in a disposable named session established the fixture flow: a fresh headless session has zero workspaces/panes, so `pane.split` alone fails with `pane_not_found` — `workspace.create` (params `cwd`/`env`/`focus`/`label` all optional; success `{type: "workspace_created", workspace, tab, root_pane}`) must come first and its `root_pane` serves as fixture pane A, then `pane.split` (direction required) creates pane B; `pane.split` has no command field (correcting the P3-T10 ledger wording at closeout); `pane.report_agent` (required params `pane_id`/`source` (free string)/`agent`/`state` (enum idle/working/blocked/unknown), optional `agent_session_id`/`agent_session_path`/`message`/`seq`) is the schema-documented client-reporting hook — reported agents appear in `agent.get`/`agent.list`/`session.snapshot` with real `agent_status` and `state_change_seq` increments; socket-schema `agent.start` kind is a free string (only the CLI restricts it to a 22-value enum, 11 installed on this machine) so the fixture strategy avoids depending on any agent CLI; `pane.wait_for_output` matches the input echo, so completion markers must use `echo "X-READY-$(date +%s)"` matched against regex `X-READY-[0-9]+` (only executed output contains the expanded timestamp); probe run proved parallel execution real (pane B finished 2s after start while pane A slept 8s, timestamp-file proof), ctrl+c cancel of A mid-sleep left no `a_leak.txt`, cross-pane input/output isolation held, and artifacts stayed per-pane (A: only `a_start.txt`; B: `b_start.txt`+`b_end.txt`)
Reusable entry point: `HerdrSocketTransport` (validated P3-T11), the existing `Request` seam and `task_status`/`cancel_task`/`resume_task` lifecycle in `forma_ai/herdr_adapter.py`, the verified aarch64 binary, and disposable uniquely named test sessions for live isolation proof
License obligation: the Apache-2.0 Herdr binary runs as an external process driven through its documented socket API; no upstream source, names, or assets are copied into product code; the adapter implements only the schema-derived wire contract
Integration decision: the adapter gains three thin methods, each 1:1 over a schema method — `open_workspace` (`workspace.create`), `open_pane` (`pane.split`), `spawn_reported_task` (`pane.report_agent` fixture agent) — with fixture agents driven by `pane.send_text` and lifecycle reusing the existing `task_status`/`cancel_task`; runtime state stays with Herdr, the product saves only correlation metadata; no product-owned runtime substitute is introduced
Planned verification: red/green unit tests for the three thin methods over a scripted fake `Request` seam; live integration tests in uniquely named sessions (`forma-p3t12-test-<uuid8>`) proving two distinct panes/runs, real parallel execution (timestamp-file proof), and no input/state/artifact/cancel leakage; full Python suite `python3 -m unittest discover tests`; `git diff --check`; evidence file under `evidence/upstream/`; Herdr ledger update including the `pane.split` wording correction; both English controls and both Chinese mirrors updated in the same closeout
Commit and push: pending
Next exact action: write the failing adapter tests for the three thin methods plus the failing live two-fixture-agent integration test, then implement the adapter methods
Secret/external-write status: no credentials, no cloud model calls, no external network access; fixture artifacts live only in disposable per-test temp directories; each live test run creates, verifies, stops, and deletes its own named session under `~/.config/herdr/sessions/`; the default session is never started or contacted

## 2026-09-01 - P3-T11 - exit

Executor: Qoder agent
Scope: bind the thin Herdr adapter to the official Herdr v0.8.2 socket transport (newline-delimited JSON over the Unix-domain socket, protocol 20, fail-closed compatibility) and prove real `ping` plus `session.snapshot` round trips against the verified binary; adapter availability becomes real transport-ping evidence (the availability half of audit finding F2)
Actions: implemented `forma_ai/herdr_transport.py` — `HerdrSocketTransport` as a `Request` callable (one connection per request; responses located by the first line carrying a `result` or `error` key, because error responses may carry an empty `id` and unsolicited event lines carry none; protocol verified via `ping` before first use, once per instance, failing closed with `HerdrProtocolError`; socket path resolution explicit path → `HERDR_SOCKET_PATH` → `HERDR_SESSION` named session → default; `HerdrTransportError` for unreachable/malformed, `HerdrRequestError(code, message)` for server error responses); added an optional probe seam to `HerdrAdapter` so `availability()` maps a validated pong to `ready`/`ping_pong_verified`, `HerdrProtocolError` to `incompatible`/`HERDR_PROTOCOL_INCOMPATIBLE`, and transport/OS errors to `unreachable`/`HERDR_SOCKET_UNREACHABLE`, while binary-presence-only behavior is exactly preserved when no probe is configured; added 24 tests — 18 in `tests/test_herdr_transport.py` (11 unit tests over a scripted fake socket factory covering envelope shape, error mapping with empty id, event-line skipping, fail-closed gate, probe rejection; 5 socket-path resolution tests; 2 live tests) and 6 adapter probe/availability tests in `tests/test_herdr_adapter.py`; live tests run the verified binary headless in unique named sessions (`forma-p3t11-test-<uuid8>`), assert the pong payload (version 0.8.2, protocol 20, capabilities `live_handoff: true`, `detached_server_daemon: false`) and a fresh `session.snapshot` (empty `agents`/`panes`), then stop and delete the session — the default session is never started; wrote `evidence/upstream/herdr-v0.8.2-socket-transport-verification-2026-09-01.md`; updated the Herdr ledger (opening statement, socket-binding gap CLOSED with evidence pointer, remaining gap narrowed to event subscription/agent integration/cancellation/recovery, new `pane.graphics.stream` runtime/schema discrepancy note)
Verification evidence: 29 tests across the two modules OK (0.837s) including both live tests; full suite `python3 -m unittest discover tests` ran 271 tests, OK, 1 skipped (expected real-Semantica integration test) — up from 247 with exactly the 24 new tests; adapter `availability()` with the live probe reports `ready`/`ping_pong_verified`; post-run residue check `~/.config/herdr/sessions/` empty and the default-session socket never created; `git diff --check` clean
Files changed: `forma_ai/herdr_transport.py` (new), `forma_ai/herdr_adapter.py`, `tests/test_herdr_transport.py` (new), `tests/test_herdr_adapter.py`, `docs/research/herdr-capability-ledger.md`, `evidence/upstream/herdr-v0.8.2-socket-transport-verification-2026-09-01.md` (new), both English controls, and both mandatory Chinese mirrors (outside the repository)
Commit and push: implementation/evidence commit `f9191bf` (`feat: bind herdr adapter to official socket transport`) includes the takeover-state control documents; this exact closeout metadata follows in the synchronization commit; both pushed to `origin/main`
Blocked items: none
Next exact action: claim P3-T12 — run two real isolated fixture agents through Herdr using only schema-documented methods (`pane.split` + `agent.start`/`pane.send_text`, never `pane.run`) with parallel execution, distinct panes/runs, and no input, state, artifact, or cancel leakage; P4-T14 remains the default next frontend task
Secret/external-write status: no credentials, no cloud model calls, no external network access; local headless Herdr test servers only, each in a uniquely named test session under `~/.config/herdr/sessions/` created, verified, stopped, and deleted by the tests themselves; the default session was never started or contacted

## 2026-09-01 - P3-T11 - takeover

Executor: Qoder agent
Starting git state: `main` clean and synchronized with `origin/main` at `3e67ae2`
Trigger: user authorization on 2026-09-01 to execute the relay-priority recommendations ("优先推进 P3-T10～T15……固定 Herdr artifact，接官方 transport"); P3-T11 claimed per the next exact action recorded identically in all four control documents; plan goals, requirements, and audit logic unchanged; P4-T14 remains pending as the default next frontend task
Scope: bind the thin Herdr adapter to the official Herdr socket transport — newline-delimited JSON over the Unix-domain socket of the pinned v0.8.2 binary, protocol 20 with fail-closed compatibility checks, and real `ping` plus `session.snapshot` transport tests against the verified binary; adapter availability becomes a real transport ping instead of binary-presence-only evidence (the availability half of audit finding F2)
Upstream search result: the bundled API schema from `herdr api schema --json` (protocol 20, schema_version 1, 91 request methods) is the authoritative wire contract and includes `ping` and `session.snapshot`; request envelope `{id, method, params}`, success envelope `{id, result: {type, …}}` discriminated on `result.type`, error envelope `{id, error: {code, message}}`; empirically confirmed against a live named test session (headless `herdr server --session <name>`): default-session socket `~/.config/herdr/herdr.sock`, named-session socket `~/.config/herdr/sessions/<name>/herdr.sock`, `herdr session stop`/`session delete` fully remove a test session; runtime nuance for the ledger: the live server accepts `pane.graphics.stream`, which the bundled schema's 91-method oneOf does not list
Reusable entry point: the existing `Request` seam in `forma_ai/herdr_adapter.py` (`_send` currently raises "Herdr request transport is not configured" — the seam contract already returns the unwrapped `result` payload, matching the mock tests), the bundled schema, the verified aarch64 binary at `~/Library/Application Support/Forma AI/cache/downloads/herdr-macos-aarch64`, and named test sessions for isolated live verification
License obligation: the Apache-2.0 Herdr binary runs as an external process driven through its documented socket API; no upstream source, names, or assets are copied into product code; the transport implements only the schema-derived wire contract
Integration decision: new `forma_ai/herdr_transport.py` implements the official wire protocol behind the existing `Request` seam — one request per connection; responses located by reading until a line contains `result` or `error` (error responses can carry an empty `id`, and unsolicited event lines carry no `id`, so pure id matching is unsafe); socket path resolution follows the ledger order explicit path → `HERDR_SOCKET_PATH` → `HERDR_SESSION` (named session) → default; every transport instance verifies the server protocol via `ping` before first use and fails closed with `HerdrProtocolError` on any mismatch; `HerdrAdapter` gains an optional probe seam so `availability()` reports a real ping result (ready / protocol-incompatible / unreachable) while binary-presence-only behavior is preserved when no probe is configured; runtime state stays with Herdr
Planned verification: red/green unit tests with a scripted fake socket (envelope unwrap, error mapping, event-line skipping, empty-id error handling, fail-closed protocol gate, path-resolution order); adapter availability tests with a fake probe; live tests against the verified binary in a uniquely named test session (server start → `ping` → `session.snapshot` → session stop → session delete), skipped when the binary is absent; full Python suite `python3 -m unittest discover tests -v`; `git diff --check`; evidence file under `evidence/upstream/`; Herdr ledger gap updates; both English controls and both Chinese mirrors updated in the same closeout
Commit and push: pending
Next exact action: write the failing transport tests (`tests/test_herdr_transport.py`) and the failing adapter probe-seam tests, then implement `forma_ai/herdr_transport.py` and the probe seam in `forma_ai/herdr_adapter.py`
Secret/external-write status: no credentials, no cloud model calls, no external network access, no destructive actions beyond the product's own test session lifecycle; one local headless Herdr test server per live test run (named test session under `~/.config/herdr/sessions/`, created, verified, stopped, and deleted by the tests themselves; the default session is never started or stopped)

## 2026-09-01 - P3-T10 - exit

Executor: Qoder agent
Scope: acquire and verify the pinned official Herdr v0.8.2 macOS aarch64 artifact and its bundled protocol schema; digest, version, protocol, schema, and license checks as installer/runtime evidence and Herdr ledger updates
Actions: added the two pinned official Herdr artifacts (`macos-aarch64`, `macos-x86_64`) to `config/upstreams.json` with a permissive macOS range (assets are architecture-discriminated, not macOS-version-gated); extended `select_artifact` with an `architecture` discriminator (artifacts declaring `architecture` require it; architecture-agnostic artifacts like oMLX keep exact prior behavior; no-architecture selection of Herdr fails closed "got 0" instead of an ambiguous match); added `--architecture` to `scripts/verify_artifact.py`; downloaded the official aarch64 binary through the product's `ResumableDownloader` into `~/Library/Application Support/Forma AI/cache/downloads/` (attempts 1–2 hit real network timeouts and attempt 3 resumed from the 2 MiB partial — the crash-safe resume path was exercised for real); ran `scripts/verify_artifact.py` (exit 0, size and SHA-256 match); executed the verified binary for `herdr --version` (`herdr 0.8.2`), `herdr api schema --json` (protocol 20, schema_version 1), and `herdr --help`; parsed the bundled schema (91 request methods, 26 event kinds, 3 subscription kinds, request/success/error/event/subscription domains all present); wrote `evidence/upstream/herdr-v0.8.2-artifact-verification-2026-09-01.md`; updated the Herdr ledger open-gaps section (first gap CLOSED with evidence pointer; new schema-discrepancy note: official v0.8.2 schema has no `pane.run` — the documented path is `pane.split` + `agent.start`/`pane.send_text`, to be used by P3-T12); created the user-requested Chinese translation of the Herdr capability ledger at the MyNote mirror directory (`Forma AI-Herdr能力清单-中文.md`, English source authoritative); closeout review corrected the ledger intro's outdated "has not yet downloaded or executed Herdr" statement to reflect the 2026-09-01 acquisition while keeping the pending-adapter-test scope
Verification evidence: five acceptance checks all pass — digest (18,969,952 bytes, SHA-256 `a5d4f4d5…e574` matched by the downloader gate, `scripts/verify_artifact.py`, and an independent `shasum -a 256`), version (`herdr 0.8.2`), protocol (20, from the binary's own schema), schema (parses; covers all five documented domains and every ledger-critical method except the noted `pane.run` discrepancy), license (Apache-2.0 per the pinned immutable release metadata; only the official release asset was acquired; no upstream source, names, or trademarks copied). Red/green: the five new architecture-selection tests failed first (`TypeError: unexpected keyword argument 'architecture'`), then passed after implementation. `git diff --check` clean. Full Python suite `python3 -m unittest discover tests -v` ran 247 tests, OK, 1 skipped (expected)
Files changed: `config/upstreams.json`, `forma_ai/artifacts.py`, `scripts/verify_artifact.py`, `tests/test_artifacts.py`, `docs/research/herdr-capability-ledger.md`, `evidence/upstream/herdr-v0.8.2-artifact-verification-2026-09-01.md` (new), both English controls, and both mandatory Chinese mirrors (outside the repository); the downloaded binary lives outside the repository under the canonical product root and is not committed
Commit and push: implementation/evidence commit `e28db7c` (`feat: pin herdr v0.8.2 artifacts with architecture selection`) includes the takeover-state control documents; this exact closeout metadata follows in the synchronization commit `5d23615` (`docs: close herdr artifact pinning task`); the ledger intro correction found in closeout review follows in a subsequent docs commit; all pushed to `origin/main`
Blocked items: none
Next exact action: claim P3-T11 — bind the thin Herdr adapter to the official socket transport (newline-delimited JSON over Unix-domain socket; protocol 20; fail closed on incompatibility) with real `ping` and `session.snapshot` transport tests against the verified binary; P4-T14 remains the default next frontend task
Secret/external-write status: no credentials, no cloud model calls, no destructive actions; one authorized HTTPS download of the official Herdr release asset from github.com with pinned-digest verification before execution; the acquired binary executed only for `--version`, `api schema --json`, and `--help` (no server start, no socket calls — that is P3-T11)

## 2026-09-01 - P3-T10 - takeover

Executor: Qoder agent
Starting git state: `main` clean and synchronized with `origin/main` at `034fe79`
Trigger: user authorization on 2026-09-01 to execute the relay-priority recommendations ("优先推进 P3-T10～T15…固定 Herdr artifact，接官方 transport"); P3-T10 claimed per the next exact action recorded identically in all four control documents; plan goals, requirements, and audit logic unchanged; P4-T14 remains pending as the default next frontend task
Scope: acquire and verify the pinned official Herdr v0.8.2 artifact (macOS aarch64 on this Apple Silicon development machine) and its bundled protocol schema; digest, version, protocol, schema, and license checks recorded as installer/runtime evidence and Herdr ledger updates
Upstream search result: Herdr v0.8.2 official release assets per the ledger's immutable evidence snapshot — `herdr-macos-aarch64` 18,969,952 bytes SHA-256 `a5d4f4d504d8b309c91f811050559300faba31258425f53c50852fc96f6ae574`, `herdr-macos-x86_64` 20,551,504 bytes SHA-256 `ab50262c8190cd7aa9056d249d255c08c328c3e8716de9cfa29db4f131b8e2c1`; the official pinned binary is the reuse decision (no product-owned runtime substitute)
Reusable entry point: `config/upstreams.json` pin manifest, `forma_ai/artifacts.py` selection/verification, `forma_ai/downloads.py` `ResumableDownloader` with the pinned-digest gate, `scripts/verify_artifact.py`, the Herdr ledger immutable snapshot, and the repository test suite
License obligation: acquire only the official Apache-2.0 release asset from `github.com/herdrdev/herdr`; no upstream source, names, or trademarks are copied into product code; Herdr attribution and license material obligations for distribution remain recorded in the ledger
Integration decision: pin both official macOS release assets in `config/upstreams.json` with architecture-discriminated selection (the existing selector currently distinguishes artifacts only by platform and macOS range); verify the acquired bytes before any execution; take version, protocol version, and schema from the official binary itself and fail closed on incompatibility; the socket transport binding and every runtime call remain owned by P3-T11+
Planned verification: red/green artifact-selection tests for the architecture dimension; `scripts/verify_artifact.py` digest and size output for the acquired aarch64 binary; `herdr --version`; `herdr api schema --json` parsed with protocol version recorded; evidence file under `evidence/upstream/`; Herdr ledger gap updates; `git diff --check`; full Python suite; both English controls and both Chinese mirrors updated in the same closeout
Commit and push: pending
Next exact action: write the failing architecture-selection tests, then add the pinned Herdr artifact entries to `config/upstreams.json`
Secret/external-write status: no credentials, no cloud model calls, no destructive actions; one authorized HTTPS download of the official Herdr release asset from github.com with pinned digest verification before execution, per the user-approved relay priority

## 2026-09-01 - P1-T09 - exit

Executor: Qoder agent
Scope: per-capability reuse audit of all product-owned runtime-like code in `forma_ai` (34 source files across the package root and `adapters/`), `scripts/supervisor.py`, `scripts/semantica_memory_runtime.py`, and the Swift runtime-path sources against the four upstream capability ledgers and the four P1 reuse decisions
Actions: read every audited source file end to end; recorded a 41-row disposition matrix (memory chain M1-M10, orchestration O1-O8, inference I1-I3, cloud C1-C7, install/lifecycle L1-L9, adapter protocol A1-A4) in `docs/research/product-runtime-capability-audit-2026-09-01.md`, each row citing file/line evidence, upstream entry point, license, disposition, and owning downstream task; verified every quoted line citation against the sources; corrected two citation inaccuracies found during closeout review (module count 31 → 34; `RuntimeSecrets.swift` path `Sources/RuntimeSecrets/` → `Sources/RuntimeSecurity/`)
Audit verdict: every audited capability is (a) a justified product-owned policy/orchestration/lifecycle/audit/UI/protocol responsibility, (b) already a thin adapter over an upstream entry point, or (c) carrying a scheduled reduction owned by an existing planned task; no capability requires removal outside planned work and no conclusion requires changing a plan goal, requirement, or audit gate; no holaOS code, assets, or names exist in any audited path
Findings: F1 retrieval seam bypassing the Semantica retrieval surface (`adapters/semantica.py:46-54`, owned by P6-T01/T02); F2 Herdr correlation held in in-memory dicts plus binary-presence-only availability (`herdr_adapter.py:62-64`, `:66-93`, owned by P3-T10/T11/T13/T15); F3 actual cloud cost computed but never checked against the approved ceiling (`deepseek_adapter.py:133-174`, `cloud_approval.py:70-95`, owned by P5); F4 confirmed-content duplication in governed memory (owned by P6-T01/T02). All four map to existing tasks; no new task IDs were created
Verification evidence: coverage check — the audit matrix inventories all 34 `forma_ai` source files plus both script entrypoints and the Swift runtime path (`SupervisorProtocol.swift`, `RuntimeSecurity/RuntimeSecrets.swift`, `LifecycleContract/ProductManifest.swift`); every row cites file/line evidence; `git diff --check` clean; full Python suite `python3 -m unittest discover tests -v` ran 242 tests, OK, 1 skipped (expected)
Files changed: `docs/research/product-runtime-capability-audit-2026-09-01.md` (new), both English controls, and both mandatory Chinese mirrors (outside the repository)
Commit and push: implementation/evidence commit `fb2deb4` (`docs: add product runtime capability audit`) pushed to `origin/main` (first push attempt timed out on a github.com connection failure; succeeded on retry); this exact closeout metadata follows in the synchronization commit
Blocked items: none
Next exact action: claim P3-T10 — pin the Herdr artifact digest and bind the official socket transport per the user-approved relay priority; P4-T14 remains the default next frontend task
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; read-only code audit plus documentation edits

## 2026-09-01 - P1-T09 - takeover

Executor: Qoder agent
Starting git state: `main` clean and synchronized with `origin/main` at `dcc1b7c`
Trigger: user authorization on 2026-09-01 to execute the relay-priority recommendations; P1-T09 runs ahead of P4-T14 under the master plan's allowed execution order (audit gates may run before or inside the relevant frontend slice and must finish before adapter implementation). Plan goals, requirements, and audit logic are unchanged; P4-T14 remains pending as the default next frontend task.
Scope: per-capability audit of all product-owned runtime-like code in `forma_ai` and `prototypes/packaging` Swift sources against the four upstream capability ledgers (`upstream-matrix.md`, `herdr-capability-ledger.md`, `holaos-capability-ledger.md`, `license-matrix.md`) and the four P1 reuse decisions in `docs/decisions.md`
Upstream search result: completed at ledger level — Semantica `v0.6.7` owns confirmed memory/decision/provenance surfaces; Herdr `v0.8.2` owns multi-agent execution state; oMLX `v0.6.3` owns local inference and embeddings; holaOS capabilities are parity references pending pinned-source mapping. This task audits product code against those maps and records entry points, license obligations, and integration decisions per capability
Reusable entry point: existing capability ledgers, reuse decisions, `forma_ai` module inventory, Swift protocol/app sources, and the repository test suites as verification evidence
License obligation: audit only; no upstream source, assets, names, or trademarks are copied; audit conclusions must preserve the recorded license boundaries (holaOS external-install-only, Semantica/Herdr/oMLX bundle candidates with notices)
Integration decision: every product-owned runtime-like capability must end the audit as (a) justified product-owned policy/orchestration/UI/lifecycle/audit responsibility, (b) a thin adapter over an upstream entry point, or (c) scheduled for removal or freeze inside existing downstream tasks (P3-T10+, P6-T01+, P4-T14+, P5, P7); no new runtime implementation is added by this audit task
Planned verification: capability inventory covers every `forma_ai` module and Swift runtime-path source; each audit row cites file/line evidence, upstream entry point, license, decision, and owning task; `git diff --check`; both English controls and both Chinese mirrors updated in the same closeout
Commit and push: pending
Next exact action: inventory `forma_ai` modules and Swift runtime sources, then write the per-capability audit matrix
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; read-only code audit plus documentation edits

## 2026-09-01 - P4-T13 - exit

Executor: Codex root agent
Scope: final bilingual History list, task detail, lifecycle distinction, execution summary, recovery decision, and audit-boundary Preview
Actions: added a fail-closed `HistoryRecoveryPreviewContract`; rendered interrupted, blocked, failed, partial, cancelled, completed, and unknown examples; connected History navigation and shared supervision projection; preserved selected task across live language switching; removed an upstream internal name found during window review
Red/green evidence: the target test first failed because `HistoryRecoveryPreviewContract` was absent; after implementation it passed, and the final full Swift package passed 42 tests with 2 real-Keychain tests skipped
Isolation evidence: the new surface contains no command client, RuntimeSecurity, Keychain, network, process, file picker, persistence, resume, retry, cancellation, or force-termination call; the immutable contract explicitly disables every runtime action and persisted-history read; production still defaults to `ManifestOverview`
Localization evidence: every new title, lifecycle label, reason, timeline entry, recovery choice, truth boundary, and action comes from shared bilingual `ProductCopy`; switching Chinese to English retained History and the selected interrupted task
Walkthrough evidence: normal-speed window review opened History, inspected multiple lifecycle examples, switched live to English without selection reset, and verified recovery controls are labeled as decision Preview only; visual review caught and removed the upstream name before final verification
Visual evidence: exact-window screenshots `evidence/ui/product-preview-history-recovery-zh-2026-09-01.png` and `evidence/ui/product-preview-history-recovery-en-2026-09-01.png` verify the bilingual list/detail/recovery shape and persistent synthetic-data disclosure
Files changed: lifecycle presentation contract/test, daily Preview navigation/supervision integration, new History/recovery SwiftUI and shared bilingual copy, two screenshots, both English controls, and both mandatory Chinese mirrors
Commit and push: implementation/evidence commit `5a06fea` (`feat: add bilingual history recovery preview`) pushed to `origin/main`; this exact closeout metadata follows in the synchronization commit
Evidence boundary: all seven tasks, agents, artifacts, checkpoints, approvals, and recovery decisions are deterministic in-memory presentation; no persisted history is read and no session is resumed, retried, cancelled, reconciled, or terminated
Blocked items: none
Next exact action: claim P4-T14 and build bilingual governed-memory review surfaces from Semantica-derived fixtures without creating another memory authority
Secret/external-write status: no credentials, cloud calls, downloads, attachment reads, history persistence, runtime recovery, approvals, or destructive actions

## 2026-09-01 - P4-T13 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `e3c7cc5`
Scope: build the final bilingual History list, task detail, lifecycle distinction, and recovery-decision Preview without reading persisted history or invoking runtime recovery
Upstream search result: Herdr remains authoritative for real session state, cancellation, resume, reconciliation, recovery, and handoff; Semantica remains authoritative for governed evidence; no upstream runtime behavior is duplicated in this task
Reusable entry point: `DailyWorkbenchPreview`, shared `ProductCopy`, `ProductPreviewProvider`, and the existing persistent synthetic-data disclosure
License obligation: no upstream source, UI, assets, names, or trademarks are copied; the work is limited to product-owned SwiftUI projection and deterministic fixtures
Integration decision: define a presentation-only history/recovery contract; distinguish interrupted, blocked, failed, partial, cancelled, completed, and unknown states; allow controls to select only an ephemeral next Preview state; prohibit persistence, resume, retry, cancellation, and force termination
Localization decision: every new title, lifecycle label, reason, timeline item, recovery choice, audit boundary, and action must come from shared Simplified Chinese/English copy and switch live without resetting the selected task
Planned verification: expected red contract test; filtered and full Swift tests; runtime-command/persistence source scan; exact-window bilingual screenshots; normal-speed lifecycle and language-preservation walkthrough; `git diff --check`
Commit and push: pending
Next exact action: add the failing History/recovery presentation contract test
Secret/external-write status: no credentials, cloud calls, downloads, attachment reads, persisted history, runtime recovery, approvals, or destructive actions

## 2026-09-01 - P4-T12C - exit

Executor: Codex root agent
Scope: connect New Task composition to the complete deterministic bilingual execution journey without invoking runtime actions
Actions: added `PreviewTransitionStage` and `ComposeToExecutionPreviewContract`; enabled typed or starter-goal entry into route review; rendered ordered route, plan, three-Agent parallel, approval, validation, and result states; added return-to-edit and next-state-only navigation; made the supervision rail follow the current Preview stage
Red/green evidence: target test first failed because `ComposeToExecutionPreviewContract` was absent; after implementation the target passed and the full Swift package passed 41 tests with 2 real-Keychain tests skipped, including a full rerun after the approval-field correction
Isolation evidence: transition surfaces contain no SupervisorClient, RuntimeSecurity, Keychain, URLSession, FileManager, Process, socket, submit, approve/reject method, or file-picker dependency; the contract forbids runtime actions, approval execution, and persistence; production still defaults to runtime `ManifestOverview`
Localization evidence: every new stage, explanation, Agent role/state, approval field, artifact, validation, result, and action comes from shared `ProductCopy`; switching from Chinese to English at the final Result state preserved the stage and user-entered goal
Walkthrough evidence: accessibility-driven normal-speed traversal entered a synthetic goal and visited route review → plan → parallel work → approval → validation → result; the Approval inspection found and corrected a destination/effect semantic mismatch before closeout
Visual evidence: exact-window screenshots `evidence/ui/product-preview-compose-to-result-zh-2026-09-01.png`, `evidence/ui/product-preview-compose-to-result-en-2026-09-01.png`, and `evidence/ui/product-preview-compose-approval-en-2026-09-01.png` verify bilingual final state and the special approval boundary; one wrong-window capture was immediately overwritten and not retained as evidence
Files changed: lifecycle transition contract/test, daily Preview integration, new execution-journey SwiftUI, shared bilingual copy, three screenshots, both English controls, and both mandatory Chinese mirrors
Commit and push: implementation/evidence commit `c003459` (`feat: connect bilingual task journey preview`) pushed to `origin/main`; this exact closeout metadata follows in the synchronization commit
Evidence boundary: all agents, artifacts, validations, approval effects, and results are deterministic synthetic presentation; no Herdr session, model inference, memory operation, workflow/tool call, cloud transmission, external write, or task history is created
Design influence: frontend-design preserved the task-to-supervision split and made the seven-stage rail the memorable orientation device; visual inspection, not tests alone, caught and corrected the approval semantics
Blocked items: none
Next exact action: claim P4-T13 and build bilingual History and recovery Preview surfaces
Secret/external-write status: no credentials, cloud calls, downloads, attachment reads, persistence, approvals, runtime execution, or destructive product actions

## 2026-09-01 - P4-T12C - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `a120153`
Scope: connect the bilingual New Task shell to a deterministic Preview journey covering compose, route review, plan, parallel execution, approval, validation, and result without runtime submission
Upstream search result: Herdr remains authoritative for real agent plans/states/artifacts; oMLX/cloud providers for inference; Semantica for governed evidence; holaOS for reusable workflow/tool capabilities. This task only presents repository-defined shapes and ephemeral navigation, so no upstream behavior is reimplemented
Reusable entry point: `DailyWorkbenchPreview`, shared `ProductCopy`, `ProductPreviewProvider` presentation vocabulary, and the existing permanent Preview isolation banner
License obligation: no upstream UI/source/assets/brands are copied; only product-owned native SwiftUI and synthetic presentation data are added
Integration decision: add an immutable transition contract with exactly ordered stages; starting requires user text or a synthetic starter selection; every control advances only to the next in-memory Preview state or returns to editing; approval is described but never performed
Localization decision: every new stage, state, action, Agent role, approval scope, artifact, validation, and result string must come from the shared Simplified Chinese/English copy authority and switch live without resetting the stage
Planned verification: expected red contract failure; filtered/full Swift tests; source isolation and production-default scans; both-language final-state screenshots; normal-speed compose-to-result walkthrough including language switch; `git diff --check`
Commit and push: pending
Next exact action: add the failing ordered transition contract test
Secret/external-write status: no credentials, cloud calls, downloads, attachment reads, persistence, approvals, runtime execution, or destructive actions

## 2026-09-01 - P4-T12B - exit

Executor: Codex root agent
Scope: make the final daily shell and pre-task New Task workspace visible and manually testable in both supported languages
Actions: added `DailyWorkbenchSurfaceContract`, a DEBUG-only `--daily-workbench-preview`, shared language-keyed `ProductCopy`, primary navigation, honestly labeled synthetic recent-task sample, outcome composer, inert context-entry explanation, local/cloud-proposal route summary, explicit privacy boundary, starter outcomes, and a collapsible supervision rail
Red/green evidence: target test first failed because `DailyWorkbenchSurfaceContract` was absent; after implementation the target passed and the full Swift package passed 40 tests with 2 real-Keychain tests skipped
Isolation evidence: daily Preview source has no SupervisorClient, RuntimeSecurity, Keychain, URLSession, FileManager, Process, socket, submit, approval, file-picker, or upstream-runtime dependency; production remains `ManifestOverview` outside explicit DEBUG arguments
Localization evidence: all new visible copy except the product name is served by the shared language-keyed copy authority; the running Language menu switched the complete visible shell between Simplified Chinese and English
Visual evidence: window-only screenshots `evidence/ui/product-preview-daily-shell-zh-compact-2026-09-01.png`, `evidence/ui/product-preview-daily-shell-zh-2026-09-01.png`, and `evidence/ui/product-preview-daily-shell-en-2026-09-01.png` verify compact/regular Chinese and regular English layouts; the supervision rail was also collapsed and its localized re-expand control verified through accessibility inspection
Files changed: daily Preview/localization SwiftUI, app DEBUG routing, lifecycle contract/test, three screenshots, accepted frontend plans, both English controls, and both mandatory Chinese mirrors
Commit and push: implementation/evidence commit `b672316` (`feat: build bilingual daily workbench preview`) pushed to `origin/main`; this exact closeout metadata follows in the synchronization commit
Evidence boundary: Preview input is ephemeral; context does not open or read files; recent history is explicitly synthetic; task-plan submission is disabled; no Herdr, oMLX/cloud, Semantica, or holaOS runtime capability is proved
Design influence: frontend-design kept a restrained native editorial workbench with the memorable task-to-supervision split, strong empty-state truth, and minimal operational chrome rather than a generic chat or decorative dashboard
Blocked items: none
Next exact action: claim P4-T12C and connect deterministic bilingual compose-to-execution Preview states without runtime submission
Secret/external-write status: no credentials, cloud calls, downloads, attachment reads, persistence, runtime execution, or destructive product actions

## 2026-09-01 - P4-T12B - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `a534888`
Scope: build the final daily product shell and New Task workspace as a read-only DEBUG Preview; every user-visible frontend string must support Simplified Chinese and English switching
Upstream search result: the daily native shell, language switching, task composition presentation, privacy explanation, context attachment affordance, and supervision-rail layout are Forma AI presentation responsibilities; Herdr still owns agent/runtime state, oMLX/cloud own inference truth, Semantica owns governed memory, and holaOS owns reusable workflow/tool capabilities
Reusable entry points: existing `WorkbenchSurfaceContract`, `ProductPreviewProvider`, route vocabulary, model selection contract, and DEBUG preview boundary; future runtime binding remains separate command/provider code
License obligation: no upstream UI, assets, copy, source, or branding will be copied; native SwiftUI controls and product-owned copy only
Integration decision: add a dedicated `--daily-workbench-preview` surface with deterministic empty/recent-task presentation, a central outcome composer, local-first route/privacy summary, context attachment affordance, and collapsible supervision rail; controls remain navigation/presentation only and never submit, attach, read, or write data
Localization decision: all new visible strings are served through one language-keyed copy authority; the surface exposes an explicit language switch, and both languages are required verification evidence
Plan: accepted `docs/plans/2026-09-01-first-run-product-shell.md`, Task 2, extended by the user's project-wide bilingual-switchable frontend requirement
Planned verification: expected red contract failure; filtered/full Swift tests; Chinese/English coverage; no-command/upstream-name/production-default scans; compact and regular window review in both languages; `git diff --check`
Commit and push: pending
Next exact action: add the failing bilingual daily-shell presentation contract test
Secret/external-write status: no credentials, cloud calls, downloads, file attachment reads, persistence, runtime execution, or destructive actions

## 2026-09-01 - P4-T12A-C1 - exit

Executor: Codex root agent
Scope: correct the English-only first-run Preview before starting the daily shell
Actions: added an explicit pre-onboarding `简体中文`/`English` choice, a supported-language lifecycle contract, complete localized copy for all seven steps, localized navigation/actions/boundary text, and an in-flow language switch
Red/green evidence: the target test first failed because the language-selection and supported-language contract fields were absent; after implementation the target passed and the full Swift package passed 39 tests with 2 real-Keychain tests skipped
Isolation/copy evidence: both language markers and the no-separate-upstream-deployment promise are present; first-run source contains no oMLX, Herdr, Semantica, holaOS, SupervisorClient, URLSession, FileManager, Process, or Keychain dependency; production remains `ManifestOverview` outside explicit DEBUG Preview
Visual evidence: window-only screenshots `evidence/ui/product-preview-language-choice-2026-09-01.png`, `evidence/ui/product-preview-first-run-zh-2026-09-01.png`, and `evidence/ui/product-preview-first-run-en-2026-09-01.png` verify the choice page and both localized onboarding surfaces
Files changed: first-run SwiftUI, lifecycle contract/test, three screenshot evidence files, both English controls, and both mandatory Chinese mirrors
Commit and push: implementation/evidence commit `3b57884` (`feat: localize first-run preview`) pushed to `origin/main`; this exact closeout metadata follows in the synchronization commit
Evidence boundary: selection is intentionally ephemeral in this read-only Preview; persisted first-run completion and later Settings language changes remain product-shell/runtime work
Blocked items: none
Next exact action: claim P4-T12B and build the final daily shell/New Task workspace
Secret/external-write status: no credentials, cloud calls, downloads, permission mutation, runtime execution, or destructive product actions

## 2026-09-01 - P4-T12A-C1 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `3575a59`
Trigger: user manual review found the first-run assistant English-only and required an explicit Simplified Chinese/English choice on opening
Scope: add language selection before onboarding and localize the complete seven-step first-run surface; do not proceed to P4-T12B until both languages are verified
Upstream search result: localization and first-run language preference are product-owned native presentation concerns; no upstream runtime capability is duplicated or invoked
Reusable entry point: SwiftUI locale-aware product copy only; future persistence belongs to General settings/onboarding state, not this read-only Preview correction
License obligation: no upstream code, copy, asset, or brand is reused
Integration decision: first view offers `简体中文` and `English`; system language may later determine recommendation, but the user makes an explicit Preview selection; all visible onboarding copy follows the selected language
Planned verification: red language contract; filtered/full Swift tests; Chinese/English string coverage scan; both-language window review; production-default and no-command scans; `git diff --check`
Commit and push: pending
Next exact action: add failing supported-language and explicit-selection contract assertions
Secret/external-write status: no credentials, cloud calls, downloads, permission mutation, runtime execution, or destructive actions

## 2026-09-01 - P4-T12A - exit

Executor: Codex root agent
Scope: make the final first-launch product shape visible without asking users to deploy upstream projects
Actions: added the seven-step first-run contract and a DEBUG-only `--first-run-preview` native assistant covering welcome, privacy, product-managed local AI preparation, recommended model, progressive macOS permissions, optional cloud, and first task; the ordinary copy presents Forma AI as one managed product
Red/green evidence: target test first failed because `FirstRunSurfaceContract` was absent; after implementation the target passed and the full Swift package passed 39 tests with 2 real-Keychain tests skipped
Isolation/copy evidence: first-run source contains no upstream project name, manual deployment command, installer/download call, SupervisorClient, network/filesystem/process/Keychain dependency, or real permission request; production still defaults to `ManifestOverview` outside DEBUG preview arguments
Visual evidence: window-only screenshot `evidence/ui/product-preview-first-run-2026-09-01.png` confirms the one-product promise, seven-step navigation, private-by-default/local-AI-managed/cloud-optional map, permanent Preview disclosure, and single Continue action are readable; the temporary signed app was stopped after review
Files changed: first-run/product-shell plan, `FirstRunPreview.swift`, `FormaAIApp.swift`, lifecycle preview contract/tests, screenshot evidence, both English controls, and both mandatory Chinese mirrors
Commit and push: included in the following verified P4-T12A commit and pushed to `origin/main`
Evidence boundary: presentation and copy are verified; automatic component acquisition, model recommendation, permission requests, onboarding persistence, and transition into a real task remain later runtime/product-shell tasks
Blocked items: none
Next exact action: claim P4-T12B and build the final daily shell/New Task workspace
Secret/external-write status: no credentials, cloud calls, downloads, installer execution, permission mutation, upstream runtime execution, or destructive actions

## 2026-09-01 - P4-T12A - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `931cebb`
Trigger: user correctly identified that the execution-state screenshot did not explain first launch, daily use, or whether upstream projects required manual deployment
Scope: insert and execute the final first-run assistant before History/recovery work; P4-T12B and P4-T12C will then show the daily shell and the transition into execution
Upstream search result: oMLX, Herdr, Semantica, and eligible holaOS capabilities remain managed implementation foundations; none owns Forma AI's first-run product explanation, privacy choice, macOS permission education, or novice navigation
Reusable entry points: later runtime binding will consume product lifecycle health and model recommendations; this task renders only product-owned read-only presentation and does not implement installers, downloaders, health checks, or permission APIs
License obligation: no upstream code/UI/assets/brands are copied; ordinary first-run copy must not present upstream project names or imply separate user deployment
Integration decision: a DEBUG-only explicit `--first-run-preview` assistant uses product language: prepare local AI automatically, recommend a model, explain optional cloud, request only necessary macOS permissions, then create the first task; technical component names remain advanced-diagnostics-only
Design direction: welcoming editorial-native setup with one clear promise, a compact preparation map, progressive disclosure, and a single obvious next action; it must feel like product orientation rather than an installer dashboard
Plan: `docs/plans/2026-09-01-first-run-product-shell.md`; dedicated worktree intentionally skipped because project governance requires one authoritative checkout and synchronized external mirrors
Planned verification: red first-run contract; filtered/full Swift tests; novice-copy and forbidden upstream/manual-deployment scan; explicit DEBUG argument and production-default scan; window-only screenshot review; `git diff --check`
Commit and push: pending
Next exact action: add the first-run contract red test
Secret/external-write status: no credentials, cloud calls, downloads, installer execution, permissions mutation, upstream runtime execution, or destructive actions; repository UI/tests, local preview screenshot, and mandatory Chinese mirror synchronization only

## 2026-09-01 - P4-T12 - exit

Executor: Codex root agent
Scope: deliver the first visible final-shape Product Preview task execution workspace
Actions: added a six-section presentation contract and a dedicated native SwiftUI surface with a persistent accessible Preview disclosure, deterministic scenario picker, goal/route identity, five-step execution rail, adaptive parallel-agent cards, scoped approval explanation, artifact validation, and explicit result/unresolved-evidence states; production still initializes `ManifestOverview`
Red/green evidence: the target test first failed because `PreviewWorkspaceSurfaceContract` was absent; after implementation the filtered test passed and the full Swift package passed 38 tests with 2 real-Keychain tests skipped
Isolation evidence: source scan found no submit/approve/reject, SupervisorClient, RuntimeSecurity, Keychain, URLSession, FileManager, Process, adapter, or upstream command call in `ProductPreviewWorkspace.swift`; Preview is selected only inside `#if DEBUG` through explicit `--product-preview`
Visual evidence: raw `swift run` was correctly rejected because macOS classified it background-only and screenshots showed another app; the same DEBUG binary was then placed in a temporary signed app bundle, explicitly launched with Preview, and captured window-only at `evidence/ui/product-preview-task-thread-2026-09-01.png`; manual review confirmed the disclosure, route, execution rail, three distinct Agent states, approval scope, empty artifact truth, and no false final result are readable in one window
Files changed: `ProductPreviewWorkspace.swift`, `FormaAIApp.swift`, `ProductPreviewProvider.swift`, `ProductPreviewProviderTests.swift`, window-only screenshot evidence, both English control documents, and both mandatory Chinese mirrors
Commit and push: included in the following verified P4-T12 commit and pushed to `origin/main`
Evidence boundary: screenshot and tests prove presentation, compilation, isolation, and visible state distinction only; they do not prove real Herdr execution, oMLX/cloud inference, Semantica evidence, holaOS adaptation, or final cross-state/accessibility acceptance
Design influence: the frontend-design skill produced a refined industrial native workbench with a calm execution rail, dense evidence panels, restrained material depth, and symbol-plus-text states; macOS conventions, accessibility, and resize behavior took precedence over web font guidance
Blocked items: none
Next exact action: claim P4-T13 and build final History and recovery surfaces from the read-only presentation authority
Secret/external-write status: no credentials, cloud calls, downloads, upstream runtime execution, or destructive actions; temporary local app launch was stopped after window capture

## 2026-09-01 - P4-T12 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `f8c3905`
Scope: render the final task workspace and multi-agent execution thread from the isolated read-only preview presentation; include goal, route, agent state, approval scope, artifacts, validation, result, and unresolved evidence
Upstream search result: Herdr already owns agent/task/pane state and artifacts; oMLX/cloud providers own inference results; Semantica owns governed evidence; holaOS owns reusable workflow/tool capability candidates; none owns Forma AI's native task-thread presentation
Reusable entry points: render only the upstream-shaped presentation fields already frozen in `ProductPreviewProvider`; no lifecycle, inference, memory, or workflow behavior is implemented in SwiftUI
License obligation: use only product-owned native controls and symbols; copy no upstream UI, source, assets, branding, or trademark
Integration decision: add a dedicated preview-only SwiftUI surface selected only by an explicit `--product-preview` development argument; production initialization remains the existing runtime workbench and never falls back to preview
Design direction: refined industrial native workbench with a calm execution rail, dense but readable evidence panels, state conveyed by symbol plus text, and restrained material depth; macOS accessibility and resizing take precedence over web-specific font guidance
Planned verification: red visible-structure contract test; filtered/full Swift tests; source scans for persistent disclosure, explicit preview argument, production default, all required sections, and no preview-triggered command calls; build and foreground screenshot review; `git diff --check`
Commit and push: pending
Next exact action: add the P4-T12 visible-structure red test and observe the expected missing contract
Secret/external-write status: no credentials, cloud calls, downloads, upstream runtime execution, or destructive actions; repository UI/tests, local build/launch screenshot, and mandatory Chinese mirror synchronization only

## 2026-09-01 - P4-T11 - exit

Executor: Codex root agent
Scope: implement and verify the explicit read-only Product Preview presentation provider
Actions: added immutable presentation value types and eight deterministic repository-defined scenarios; every scenario, task, agent, approval, and artifact identity is synthetic and preview-prefixed; the provider exposes lookup and data only, declares runtime fallback forbidden, and has no command surface
Red/green evidence: the filtered test first failed because `ProductPreviewProvider` and `PreviewTaskState` were missing; after implementation, both targeted tests passed and the full Swift package passed 37 tests with 2 real-Keychain tests skipped
Isolation evidence: the provider source imports no module and contains no Supervisor, RuntimeSecurity, Foundation networking/filesystem, Keychain, process, socket, adapter, persistence, or write dependency; `git diff --check` passed
Files changed: `ProductPreviewProvider.swift`, `ProductPreviewProviderTests.swift`, both English control documents, and both mandatory Chinese mirrors
Commit and push: included in the following verified P4-T11 commit and pushed to `origin/main`
Evidence boundary: the provider is not yet connected to the visible SwiftUI workbench and proves no upstream runtime capability; P4-T12 owns the first final-shape execution surface
Design influence: the frontend-design skill kept the model presentation-led and intentionally product-specific, while native macOS conventions and the accepted isolation contract overrode web-specific aesthetic guidance
Blocked items: none
Next exact action: claim P4-T12 and render the final task execution line from the read-only presentation model
Secret/external-write status: no credentials, cloud calls, downloads, runtime execution, or destructive actions; repository code/tests and mandatory Chinese mirror synchronization only

## 2026-09-01 - P4-T11 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `fd41069`
Scope: implement the explicit read-only Product Preview presentation provider and isolation tests; do not yet redesign the visible task-execution screen
Upstream search result: Herdr, Semantica, oMLX, and holaOS own the runtime facts represented by preview scenarios, but none owns the native Swift presentation provider; the P4-T10 contract fixes that provider as product-owned and synthetic
Reusable entry points: only the already-documented upstream-shaped identifiers, state vocabulary, capability names, and presentation fields are reused in this task; no upstream runtime API is invoked
License obligation: no upstream source, frontend, asset, trademark, or bundled artifact is copied; existing release notice gates remain unchanged
Integration decision: add an immutable in-memory `ProductPreviewProvider` with deterministic `preview-*` identities and a permanent isolation label; expose data only, with no command methods or dependencies on Supervisor, RuntimeSecurity, Foundation networking/filesystem APIs, Keychain, or adapters
Planned verification: red test first; deterministic scenario/state coverage; source dependency/forbidden-call scan; filtered and full Swift tests; `git diff --check`
Commit and push: pending
Next exact action: write the P4-T11 isolation tests and observe the expected missing-provider failure
Secret/external-write status: no credentials, cloud calls, downloads, runtime execution, or destructive actions; repository code/tests and mandatory Chinese mirror synchronization only

## 2026-09-01 - P4-T10 - exit

Executor: Codex root agent
Scope: audit the current frontend against the target-release experience and freeze the upstream-authority-bound Product Preview presentation contract
Actions: created a screen-by-screen final-shape gap matrix covering New Task, execution, parallel agents, approvals, artifacts, final result, History/recovery, eight Settings sections, and first run; defined deterministic preview scenarios, state vocabulary, provider separation, accessibility requirements, and a permanent synthetic-data/no-runtime-action label
Upstream decision: Herdr remains lifecycle and artifact authority, Semantica remains governed-memory authority, oMLX remains local inference authority, and holaOS remains a reusable non-visual capability source pending its pinned adapter audit; Forma AI owns only the native presentation and integration boundary
Verification: `git diff --check` passed; required authority and isolation anchors were present; `swift test --package-path prototypes/packaging` passed 35 tests with 2 real-Keychain tests skipped
Files changed: `docs/research/frontend-final-shape-gap-matrix.md`, `docs/contracts/product-preview-presentation.md`, both English control documents, and both mandatory Chinese mirrors
Commit and push: included in the following verified P4-T10 commit and pushed to `origin/main`
Evidence boundary: this task defines and verifies presentation requirements only; it does not prove real Herdr execution, Semantica persistence, oMLX inference, holaOS adaptation, cloud execution, or release readiness
Blocked items: none
Next exact action: claim P4-T11 and implement the read-only Product Preview provider plus isolation tests
Secret/external-write status: no credentials, cloud calls, downloads, runtime execution, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-09-01 - P4-T10 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `9474f61`
Scope: audit the current SwiftUI against the bilingual target-release guide and define the final presentation contract before product UI implementation
Upstream search result: Herdr ledger provides agent identity/state/wait/cancel/resume/artifact surfaces; holaOS ledger provides workflow/application/tool capability candidates; Semantica owns confirmed memory; oMLX owns inference/model state; no upstream owns the Forma AI native macOS presentation
Reusable entry points: Herdr snapshot/events/agent/pane APIs; holaOS runtime/harness/tool surfaces pending P4-T07A pin verification; Semantica AgentContext adapter surfaces; oMLX health/models/chat/embedding APIs
License obligation: Herdr Apache-2.0 notices; holaOS modified license and no copied frontend/assets; Semantica and oMLX obligations remain pinned-release gates; Product Preview contains no upstream code or assets
Integration decision: create only a product-owned presentation specification and explicit read-only preview boundary; no scheduler, memory store, model server, workflow engine, or runtime state machine
Planned verification: every target-guide journey maps to a screen, state, upstream authority, and preview/runtime boundary; current gaps are explicit; Swift baseline remains green; `git diff --check`
Commit and push: pending
Next exact action: write the gap matrix and presentation contract
Secret/external-write status: no credentials, cloud calls, downloads, runtime execution, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-09-01 - P0-T11 - exit

Executor: Codex root agent
Scope: revise execution around strict upstream reuse and early manual testing of the final frontend shape
Actions: added the controlling frontend-first/upstream-reuse design; required upstream search, reusable entry point, license obligation, and integration decision before implementation; separated the verified Herdr mock/contract slice from new real-runtime tasks; replaced the planned competing task-state store with a Herdr-authoritative metadata projection; rewrote Semantica work around audit and real reuse; added P4-T10 through P4-T17 for an explicit read-only Product Preview and complete final-form frontend review
Decision: use frontend-shape-first vertical slices, not a frontend-only waterfall; preview data is deterministic, read-only, visibly labeled, cannot call runtime/network/Keychain/write paths, and cannot satisfy runtime acceptance
Verification: English/Chinese strategy and task summaries agree; P3 real gates, P6 Semantica authority, P7 Herdr authority, preview/runtime separation, and four mandatory upstream-evidence fields are explicit; `git diff --check` passed
Files changed: new design plan, English master plan/handoff, and both mandatory Chinese mirrors
Commit and push: included in the following verified plan-adjustment commit
Blocked items: none
Next exact action: claim P4-T10 and audit the current SwiftUI against the target-release guide before product UI changes
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-09-01 - P0-T11 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `a7fa026`
Scope: adjust the execution plan so existing capabilities in Semantica, holaOS, Herdr, and oMLX are never reimplemented, while moving visible final-form frontend work earlier for continuous user testing
Requirements: separate mock/contract completion from real upstream integration; prevent a second runtime or memory authority; expose the final product shape early through explicitly synthetic preview data; bind each completed surface to its upstream authority in the following vertical slice
Design: frontend-shape-first, upstream-contract-bound vertical slices; product-owned code is limited to native UI, permission/approval, audit correlation, lifecycle, and the thinnest required adapters; every implementation task records upstream search result, reusable entry point, license obligation, and integration decision
Planned verification: bilingual plan parity, task dependency and authority scan, `git diff --check`; no product code in this governance unit
Commit and push: pending
Next exact action: add the revised design and granular tasks, then close P0-T11 and claim P4-T10
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-09-01 - P8-T05 - exit

Executor: Codex root agent
Scope: deliver equivalent Chinese and English target-final-release product introductions and user guides plus a novice-user acceptance script
Actions: added two structurally equivalent 17-section guides covering product identity, users, complete capabilities, advantages, permanent boundaries, unsupported responsibilities, first launch, interface, task writing, approvals, multi-agent use, memory, privacy, recovery, lifecycle, FAQ, and a first-week path; added a ten-journey novice acceptance script; linked all documents from README
Evidence boundary: each guide is explicitly labeled as documentation for the fully completed, release-accepted product; before release it defines target experience and acceptance rather than claiming the current development build implements every described capability
Verification: both guides have matching 17-section structures; English guide has 2,758 words and Chinese guide 6,729 characters; target-release disclaimers and README links are present; `git diff --check` passed; Python suite passed 242 tests with 1 opt-in Semantica integration skip; Swift suite passed 35 tests with 2 real-Keychain skips
Files changed: `README.md`, both guides, `docs/runbooks/novice-acceptance.md`, both English control documents, and both mandatory Chinese mirrors
Commit and push: content commit `74bdba6 docs: add bilingual target release user guides`; closeout metadata follows in the synchronization commit and both will be pushed to `origin/main`
Design influence: the copywriting skill shaped an outcome-first orientation, clear first action, objection handling, and durable trust boundaries without sales claims or invented proof
Blocked items: actual novice-user execution remains a release acceptance gate; document completion is not user-test completion
Next exact action: P4-T07A verifies the separately installed holaOS non-visual adapter boundary without bundling uncleared UI/assets
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-09-01 - P8-T05 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `afdbd6c`
Scope: create equivalent Chinese and English target-release user guides and a novice-user acceptance script; add discoverable README links
Requirements: describe the fully completed product rather than the current development slice; explain what Forma AI is, what it can do, advantages, permanent capability boundaries, unsupported responsibilities, first launch, safe daily use, recovery, and how to get better results
Design: label both guides as target final-release documents until release acceptance passes; use an outcome-first orientation, a 10-minute first-launch path, capability map, task-writing pattern, approval/privacy model, durable limitations, recovery, best practices, and FAQ; keep Chinese and English structurally and semantically equivalent
Planned verification: required files and matching section anchors; future-state disclaimer; claims traceability to product requirements; README links; `git diff --check`; full Python and Swift suites
Commit and push: pending
Next exact action: draft the target-release bilingual guides and novice acceptance script
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-08-31 - P0-T10 - exit

Executor: Codex root agent
Scope: repair the README product-role conflict and stale current Git baseline across the bilingual control set
Actions: made the product-owned native workbench the explicit default entry in README; reclassified holaOS as a non-visual capability/workflow source and optional separately installed advanced interface; replaced stale current-state Git claims with the verified `709fee0` takeover fact while preserving dated historical evidence; returned the baton to P4-T07A
Verification: role-conflict scan found no active claim that holaOS owns the default UI; Python suite passed 242 tests with 1 opt-in real Semantica test skipped; Swift suite passed 35 tests with 2 real-Keychain tests skipped; bilingual task/status/next-action/Git facts were inspected; `git diff --check` passed
Files changed: `README.md`, both English control documents, and both mandatory Chinese mirrors
Commit and push: repair commit `9454cdd docs: repair product role and git baseline drift`; closeout synchronization is recorded in the following commit and both will be pushed to `origin/main`
Blocked items: none
Next exact action: P4-T07A verifies the separately installed holaOS non-visual adapter boundary without bundling uncleared UI/assets
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-08-31 - P0-T10 - takeover

Executor: Codex root agent
Starting git state: `main` clean and synchronized with `origin/main` at `709fee0`; `git fetch --all --prune` found no additional remote branch; the detached worktree at `87f067e` is already an ancestor of `main` and requires no merge
Scope: repair the README role conflict and stale current Git baseline in the bilingual control set; do not implement P4-T07A or change product behavior
Requirements: the product-owned native workbench is the default distributable UI; holaOS remains a non-visual capability/workflow source and optional separately installed adapter until redistribution is cleared; current-state fields must reflect `709fee0` without rewriting historical evidence
Design: add one governance task, update only current baton/current-worktree statements and the README component-role table, preserve dated historical commit facts, then return the baton to P4-T07A
Planned verification: repository-wide role-conflict scan; bilingual task/status/next-action/Git parity; `git diff --check`; full Python and Swift suites
Commit and push: pending
Next exact action: apply the minimal README and control-document corrections, then verify
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-08-31 - P4-T07 - documentation calibration

Executor: Codex root agent
Reason: independent audit confirmed the implementation and all eight reachable contract-driven sections, but found stale capability, commit, and baton evidence plus acceptance wording broader than the tests prove
Corrections: set CAP-12 to partial; recorded exact implementation commit `51fdfe2`; limited acceptance to Settings information architecture and reachable surface; explicitly left full Agents, Memory, Permissions, Data management and a verified first-run user flow pending
Verification: bilingual control-document parity inspection and `git diff --check`; no product code changed and the independently rerun Swift result remains 35 passed with 2 real-Keychain skips
Commit and push: `98747f6 docs: calibrate P4-T07 acceptance boundary` pushed to `origin/main`; this closeout metadata is recorded in the following synchronization commit
Next exact action: confirm the closeout synchronization is pushed and the repository is clean; P4-T07A remains pending for a separate takeover
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory Chinese mirror synchronization only

## 2026-08-31 - P4-T07 - exit

Executor: Codex root agent
Scope: complete product Settings information architecture and native SwiftUI surface
Actions: added a public eight-section Settings contract; renamed primary navigation from Settings & recovery to Settings; added a native macOS split settings surface; routed existing cloud/model, memory, runtime, and diagnostics controls to their responsible sections; the contract declares first-run setup separate and installation/recovery controls are progressively disclosed only under Diagnostics & Recovery
Verification: the target Settings contract test passed; full Swift package passed 35 tests with 2 real-Keychain tests skipped; source inspection confirmed all eight contract sections are rendered from `surfaceContract.settings.sections`, normal navigation says Settings, and setup/recovery wording exists only in the diagnostics path; `git diff --check` passed
Evidence boundary: tests prove the eight-section information architecture, reachability, and compilation, not final visual acceptance, complete functional management for Agents, Memory, Permissions, or Data, or a verified first-run user flow; `separateAssistant` is a contract statement rather than user-flow evidence, and unavailable functions remain honest explanatory states
Files changed: `ProductManifest.swift`, `ProductManifestTests.swift`, `FormaAIApp.swift`, and synchronized English/Chinese control documents
Commit and push: `51fdfe2 feat: build complete product settings surface` pushed to `origin/main`
Design influence: the frontend-design skill led to a restrained, information-dense native macOS hierarchy with section-specific summaries instead of a generic card wall; macOS platform conventions took precedence over web typography guidance
Blocked items: none
Next exact action: P4-T07A verifies the separately installed holaOS non-visual adapter boundary without bundling uncleared UI/assets
Approval needed: none
Secret/external-write status: no credentials, cloud calls, downloads, or destructive actions; mandatory control-document sync only

## 2026-08-31 - P4-T07 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized at `5a39632`; Swift baseline 34 passed with 2 real-Keychain skips
Scope: replace the setup-shaped Settings page with a normal eight-section product Settings information architecture while preserving truthful existing controls
Requirements: General; Models & Providers; Agents & Tools; Memory; Permissions & Approvals; Local Runtime; Data & Privacy; Diagnostics & Recovery; first-run setup remains separate and recovery is progressively disclosed under its named section
Design: restrained native macOS split settings surface with clear section identity, compact status summaries, and no copied upstream visual assets; existing runtime/provider controls are routed to their appropriate sections rather than duplicated
Files intended: lifecycle contract, SwiftUI app, lifecycle tests, and synchronized English/Chinese control documents
Planned verification: red contract test first, then target/full Swift tests, source inspection for eight reachable sections and separate setup/recovery semantics, `git diff --check`
Approval needed: none; UI/contract work only, no credentials, cloud calls, downloads, or destructive actions
Next exact action: write the eight-section failing contract test before implementation

## 2026-08-31 - P4-T06 - green correction

Executor: Codex root agent
Reason: the same Swift target cannot retain a permanent compile-red recovery test and still provide valid P4-T07 verification
Actions: implemented only the contract enums and immutable recovery contract for task-detail placement, visible recovery states, verified native-session resume source, fresh snapshot/revision reconciliation, and separate force-termination approval
Verification: filtered recovery test passed; full Swift package passed 34 tests with 2 real-Keychain tests skipped; `git diff --check` passed
Evidence boundary: no recovery buttons, persistence, cancellation request, process control, or duplicate Herdr lifecycle state was added
Files changed: `ProductManifest.swift` and synchronized English/Chinese control documents
Commit and push: included in the following green-correction closeout commit
Next exact action: P4-T07 starts as a separate batch for the eight-section Settings information architecture

## 2026-08-31 - P4-T06 - exit

Executor: Codex root agent
Scope: recovery-action visible-state contract red test only
Prerequisite correction: Swift compiles the full test target before filtering, so the unimplemented P4-T05 red test masked P4-T06; P4-T05 was minimally implemented as a pure contract and turned green before P4-T06 was retried
Actions: P4-T05 added contract-only history placement/source/empty-state/no-fixture semantics; P4-T06 added assertions for task-detail recovery visibility, eligible recovery states, verified native-session resume source, fresh snapshot/revision reconciliation, and separate force-termination approval
Verification: P4-T05 target passed and full Swift package passed 33 tests with 2 real-Keychain skips; after that correction, filtered P4-T06 failed exactly because `WorkbenchSurfaceContract` has no `recovery` member; `git diff --check` passed
Evidence: P4-T06 now has one independent missing-contract root cause; no persistence, static history rows, recovery buttons, real cancellation, or duplicate runtime state was added
Files changed: `ProductManifest.swift`, `ProductManifestTests.swift`, and synchronized English/Chinese control documents
Commit and push: included in the following verified correction/red-test commit
Decisions: permanent compile-red tests cannot be accumulated in one Swift target; each prerequisite contract must turn green before the next red contract is evidence
Blocked items: none
Next exact action: P4-T07 implements complete product Settings information architecture and separates it from setup/recovery
Approval needed: none
Secret/external-write status: no secrets, cloud calls, real Herdr execution, or destructive actions

## 2026-08-31 - P4-T06 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized at `22df91a` after P4-T05 red-test closeout
Scope: add the recovery-action visible-state contract red test only; do not implement static resume/cancel controls or duplicate Herdr lifecycle authority
Design: recovery is visible from task detail for blocked, failed, interrupted, and unknown states; resume requires persisted task plus verified native session and a fresh snapshot/revision reconciliation; force termination remains a separately approved action
Files intended: `ProductManifestTests.swift` plus synchronized English/Chinese control documents
Planned verification: filtered Swift test fails specifically because the workbench contract lacks recovery visibility semantics; `git diff --check`
Approval needed: none; no real cancellation, cloud call, credential, or destructive action
Next exact action: write the failing recovery contract test and capture the exact missing API

## 2026-08-31 - P4-T05 - exit

Executor: Codex root agent
Scope: task-history visible-state contract red test only
Actions: added assertions for primary-navigation placement, persisted-task-record sourcing, an explicit no-history state, and a hard prohibition on preview fixtures as history
Verification: filtered Swift test failed at compile time because `WorkbenchSurfaceContract` has no `history` member; the unresolved enum cases were direct consequences of that missing contract; `git diff --check` passed
Evidence: failure precisely identifies the absent history truth boundary; no static rows, persistence store, or second state authority was added
Files changed: `ProductManifestTests.swift` plus synchronized English/Chinese control documents
Commit and push: included in the following verified red-test commit
Decisions: P7 remains responsible for persistence implementation; P4-T05 defines only truthful visible-state requirements
Blocked items: none
Next exact action: P4-T06 adds the recovery-action visible-state red contract without implementing static recovery controls
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, real Herdr execution, or destructive actions

## 2026-08-31 - P4-T05 - primary takeover

Executor: Codex root agent
Previous owner state: the dedicated workbench task synchronized to `87f067e` but produced no file changes, tests, or takeover record during repeated waits; its worktree remained clean and it was told to stop
Scope: add the task-history visible-state contract red test only; do not implement static history entries or alter P4-T06
Design: history must live in primary navigation, read persisted task records, expose an explicit empty state, and forbid preview fixtures from masquerading as history; persistence implementation remains P7 and no second state authority is introduced
Files intended: `ProductManifestTests.swift` plus synchronized English/Chinese control documents
Planned verification: existing Swift baseline remains green; the filtered new test fails specifically because the workbench contract lacks history visibility semantics; `git diff --check`
Approval needed: none; no credentials, cloud calls, real Herdr execution, or destructive actions
Next exact action: write the failing contract test, capture the exact missing API, then close and push the red unit

## 2026-08-31 - P3-T08/P3-T09 - exit

Executor: Codex root agent
Scope: truthful parallel-Agent UI fixture plus P3 core-slice closeout
Actions: added injectable Agent task view state with stable task/run/pane identities; rendered running and blocked cards only when state is supplied; added an explicit preview fixture and `Preview fixture · not runtime evidence` label; kept the production initializer default empty
Verification: `swift test --package-path prototypes/packaging` passed 32 tests with 2 real-Keychain tests skipped; source inspection confirmed `agentTaskFixture` defaults to `[]`, only the DEBUG preview injects `parallelPreview`, and visible fixture data is labeled non-runtime evidence; `git diff --check` passed
Evidence: Swift compilation covers the app target and the existing selector/lifecycle contracts; this proves fixture rendering compatibility, not a real Herdr process or live state subscription
Files changed: `FormaAIApp.swift` plus synchronized English/Chinese control documents
Commit and push: included in the following verified P3 closeout commit
Decisions: fixture state never becomes production evidence; live Herdr state binding remains a later integration requirement
Blocked items: none
Next exact action: P4-T05 may now claim the released Swift surface and add the task-history visible-state red test
Approval needed: none
Secret/external-write status: no secrets, cloud calls, or real Herdr processes; mandatory control-document synchronization only

## 2026-08-31 - P3-T08 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized at `dc98107` after P4-T04 turned the selector contract green and released the overlapping Swift file
Scope: add a UI task-state fixture that demonstrates multiple parallel Herdr-backed agent states without presenting fixture data as runtime evidence
Design: production initializes with no agent rows; an explicitly named preview fixture supplies running and blocked examples; visible cards label the source as preview data and preserve stable task/run/pane identity fields
Files intended: `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift` plus synchronized English/Chinese control documents
Planned verification: full Swift package tests, source inspection for preview-only fixture and empty production default, and `git diff --check`
Approval needed: none; no real Herdr process, cloud call, credential, or destructive action
Next exact action: implement the minimal preview fixture and task-state cards, then verify

## 2026-08-31 - P4-T04 - parallel exit

Executor: Codex delegated workbench agent
Scope: model-selection contract, local UI state, and visible composer-toolbar selector
Actions: added automatic-local-first, local-only, and cloud-with-approval choices; bound the selector to view state; kept automatic routing executable while showing and disabling submission for preferences whose Supervisor binding is pending
Verification: filtered selector contract passed; full Swift package passed 32 tests with 2 real-Keychain tests skipped; source review confirms cloud remains guarded by Keychain credential state, exact proposal UI, and explicit Approve and run action
Evidence: tests prove the selector contract and app compile; source state proves unsupported preferences are not silently submitted; no claim is made that local-only/cloud-preference routing is wired into Supervisor yet
Files changed: `ProductManifest.swift`, `FormaAIApp.swift`, and synchronized English/Chinese control documents
Commit: `318c7e0 feat: add governed model route selector`
Push: `318c7e0` pushed to `origin/main`; this closeout metadata follows in a documentation-only commit
Decisions: automatic local-first remains the only execution-bound choice in this task; local-only and cloud-with-approval are truthful pending preferences, with visible pending status and disabled submit
Blocked items: none
Next exact action: commit and push P4-T04, notify the P3 owner to synchronize, then P4-T05 adds the history visible-state red test
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

## 2026-08-31 - P4-T04 - parallel takeover

Executor: Codex delegated workbench agent
Starting git state: clean detached worktree synchronized to primary/`origin/main` at `4e0941a`; P3-T08 remains pending and owned by the primary task
Scope: implement the model-selection contract, local UI state, and visible composer-toolbar selector; do not change P3 or claim provider readiness
Files intended: lifecycle contract, SwiftUI app, and synchronized English/Chinese control documents
Actions: repaired the stale detached baseline before claiming P4-T04; confirmed the P4-T03 red test is present and the current P3 baton is P3-T08
Verification: filtered selector test and full Swift package must pass; source/state review must prove cloud selection still requires configured credentials and separate per-request approval
Evidence: pending implementation and tests
Files changed: control documents at takeover
Commit: none yet
Push: none yet
Decisions: selector choices govern routing preference only; they cannot mark a provider ready, expose credentials, or authorize data transmission
Assumptions: current Supervisor unified-task request has no route-preference input, so P4-T04 may expose truthful local UI preference state but must label execution binding as pending until the later routing contract is extended
Blocked items: none
Next exact action: implement the contract types, add selector state/UI in the composer, keep explicit pending-binding copy, and run targeted/full Swift tests
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

## 2026-08-31 - P3-T07 - exit

Executor: Codex root agent
Scope: minimal feature-flagged Supervisor delegation to the existing Herdr adapter
Actions: added an immutable default-off feature configuration; disabled dispatch fails closed with `HERDR_EXECUTION_DISABLED`; enabled dispatch forwards the exact task envelope once to `HerdrAdapter.spawn_task`
Verification: focused supervisor tests passed 2; the first full run exposed only read-only-sandbox temporary-directory errors; after restoring the pre-existing Supervisor test body from an accidental uncommitted overwrite, the authorized rerun passed all 242 tests with 1 opt-in real Semantica integration skip; `git diff --check` passed
Evidence: the recording adapter proves exact one-time delegation; the disabled adapter is never invoked; no scheduler or duplicate runtime state was added
Files changed: `forma_ai/supervisor.py`, `tests/test_supervisor.py`, and synchronized English/Chinese control documents
Commit and push: this implementation and closeout are included in the following verified commit
Decisions: the feature is explicit and default-off; Herdr remains execution authority; this task does not claim real-process acceptance
Blocked items: none
Next exact action: P3-T08 adds a truthful UI task-state fixture for parallel agents
Approval needed: none
Secret/external-write status: no secrets, cloud calls, or real Herdr processes; mandatory control-document sync only

## 2026-08-31 - P3-T07 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized at `fa53378` after integrating and pushing P3-T06 plus P4-T03
Scope: wire the product supervisor to the existing Herdr adapter behind an explicit feature flag
Upstream boundary: reuse `HerdrAdapter.spawn_task`; do not add a scheduler, duplicate runtime state, or make Herdr execution claims while disabled
Files intended: `forma_ai/supervisor.py`, focused tests, and synchronized English/Chinese control documents
Planned verification: focused supervisor tests, full Python unittest discovery, and `git diff --check`
Approval needed: none; mock transport only, no cloud calls, credentials, or real Herdr process
Next exact action: define the fail-closed feature-flag test, implement the minimal delegation boundary, then verify

## 2026-08-31 - P4-T03 - parallel exit

Executor: Codex delegated workbench agent
Scope: model/provider selection contract red test only
Actions: added assertions for a composer-toolbar selector whose default is automatic local-first and whose choices are automatic local-first, local-only, and cloud-with-approval; cloud requires credential plus per-request approval
Verification: filtered Swift test failed at compile time because `WorkbenchSurfaceContract` has no `modelSelection` member; dependent enum cases were consequently unresolved
Evidence: the failure precisely identifies the absent selector contract; no static selector or fake provider readiness was added
Files changed: `ProductManifestTests.swift` plus synchronized English/Chinese control documents
Commit: `e287939 test: define governed model selector contract`
Push: `e287939` pushed to `origin/main`; this closeout metadata follows in a documentation-only commit
Decisions: composer selection governs routing behavior, while provider credentials/catalog details remain truthful Settings/runtime state; selecting cloud must never authorize transmission by itself
Blocked items: none
Next exact action: commit and push P4-T03; P4-T04 must implement selector contract/state and visible composer UI while preserving approval guards
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

## 2026-08-31 - P4-T03 - parallel takeover

Executor: Codex delegated workbench agent
Starting git state: clean detached worktree at `e8d7359`, pushed to `origin/main`; primary P3 task notified to synchronize before pushing
Scope: add the failing model/provider selection contract test only; do not implement UI state or alter P3
Files intended: lifecycle contract test plus synchronized English/Chinese control documents
Actions: claimed P4-T03 after P4-T02 made the first-screen workbench contract green
Verification: existing Swift baseline remains known-green; filtered new test must fail specifically because model selection is absent from the workbench contract
Evidence: pending red-test result
Files changed: control documents at takeover
Commit: none yet
Push: none yet
Decisions: the selector contract will default to automatic local-first, expose local-only and cloud-with-approval choices, and retain credential plus per-request approval for cloud
Assumptions: provider brand details remain Settings/catalog concerns; the composer selector chooses governed routing behavior rather than exposing secrets or pretending unavailable providers are ready
Blocked items: none
Next exact action: add the failing selector contract assertions and run the filtered Swift test
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

## 2026-08-31 - P4-T02 - parallel exit

Executor: Codex delegated workbench agent
Scope: implement the minimal first-screen workbench contract and bind SwiftUI default navigation to it
Actions: added `WorkbenchSurfaceContract.productDefault` with New task as the initial destination, first-screen composer placement, Supervisor unified-task binding, and separate Settings/recovery; initialized `ManifestOverview` navigation from that contract
Verification: filtered P4-T01 contract test passed; full Swift package passed 31 tests with 2 real-Keychain tests skipped; source inspection confirms task execution still calls `SupervisorClient.submitTask`
Evidence: machine tests prove the contract exists and the app consumes its initial destination; they do not prove model selection, Herdr parallel execution, history persistence, or final visual quality
Files changed: `ProductManifest.swift`, `FormaAIApp.swift`, and synchronized English/Chinese control documents
Commit: `53ab109 feat: bind first-screen workbench contract`
Push: `53ab109` pushed to `origin/main`; this closeout metadata follows in a documentation-only commit
Decisions: the contract is product-owned UI/integration behavior and does not duplicate an upstream non-visual capability; no holaOS asset or frontend code is copied
Blocked items: none
Next exact action: commit and push P4-T02, then claim P4-T03 and add the model/provider selection red test
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

## 2026-08-31 - P4-T02 - parallel takeover

Executor: Codex delegated workbench agent
Starting git state: clean detached worktree at `5fe31d0`; P4-T01 and its closeout are pushed to `origin/main`, and the primary P3 task was notified to synchronize before pushing
Scope: implement the minimal first-screen workbench contract and bind the SwiftUI default navigation to it; do not change P3 state or claim model/agent/history completion
Files intended: lifecycle contract, SwiftUI app, and synchronized English/Chinese control documents
Actions: claimed P4-T02 after the P4-T01 red test failed specifically on the absent `WorkbenchSurfaceContract`
Verification: filtered red test must turn green, full Swift package tests must pass, and source inspection must confirm unified Supervisor submission remains the task execution binding
Evidence: pending implementation and test results
Files changed: control documents at takeover
Commit: none yet
Push: none yet
Decisions: the public contract will drive the initial destination and navigation ordering; it will describe the already-real Supervisor unified submission rather than introduce a fixture executor
Assumptions: extending `LifecycleContract` is necessary because the approved P4-T01 test lives in that target, even though the original P4-T02 file column named only the app source
Blocked items: none
Next exact action: add the minimal contract type, bind `ManifestOverview` initial navigation/sidebar to it, and run targeted then full Swift tests
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

## 2026-08-31 - P4-T01 - parallel exit

Executor: Codex delegated workbench agent
Scope: first-screen task-composer contract red test only
Actions: added a lifecycle contract test requiring New task as the initial destination, the composer on the first screen, unified Supervisor task submission, and setup/recovery in separate Settings
Verification: full Swift baseline passed 30 tests with 2 real-Keychain tests skipped; the filtered new test then failed at compile time because `WorkbenchSurfaceContract` is not in scope, with the four required enum values consequently unresolved
Evidence: the failure is contract absence, not a runtime, dependency, or unrelated regression; no product implementation was added in this red-test unit
Files changed: `prototypes/packaging/Tests/LifecycleContractTests/ProductManifestTests.swift` plus synchronized English/Chinese control documents
Commit: `f04f221 test: define first-screen workbench contract`
Push: `f04f221` pushed to `origin/main`; this closeout metadata follows in a documentation-only commit
Decisions: the contract must describe truthful runtime binding and first-screen placement; a screenshot or existing SwiftUI text is insufficient acceptance evidence
Blocked items: none
Next exact action: commit and push P4-T01, then claim P4-T02 and implement the smallest contract/UI binding that turns this test green
Approval needed: none
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

## 2026-08-31 - P4-T01 - parallel takeover

Executor: Codex delegated workbench agent
Starting git state: clean detached worktree at `8e09942`, matching `main` and `origin/main`; the primary checkout remains the P3 owner
Scope: write the failing UI contract test for the first-screen task composer only; do not change P3 task state
Files intended: lifecycle contract test plus synchronized English/Chinese control documents
Actions: reviewed the current SwiftUI workbench, manifest contract, and Swift tests; confirmed a real task submission surface exists but no machine-readable first-screen workbench contract exists
Verification: targeted Swift package test must fail specifically because the composer contract is absent while existing tests remain green
Evidence: `FormaAIApp.swift` currently defaults to New task and submits through `SupervisorClient`, but the lifecycle contract exposes no first-screen task-composer declaration
Files changed: control documents at takeover
Commit: none yet
Push: none yet
Decisions: P4-T01 is a red-test-only unit; model selection, agent state, history, recovery, settings IA, and real Herdr wiring remain later tasks
Assumptions: the user's explicit parallel delegation permits P4-T01 to be `in_progress` while P3-T06 remains owned by the primary task
Blocked items: none
Next exact action: add a contract test that requires task-composer placement, truthful runtime binding, and separation from setup/recovery, then run the targeted Swift suite and preserve the expected red result
Approval needed: none; repository-local tests only
Secret/external-write status: no secrets, credentials, cloud calls, or destructive actions

This is the authoritative handoff document for agent takeover, interruption recovery, and cross-tool continuity.

## 2026-08-31 - P2-T08 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `5061ba7`
Scope: repair stale handoff/worktree statements and make the P2 exit gate truthful
Files intended: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Planned verification: adapter-contract unit tests, downstream conformance ownership audit, `git diff --check`, and final Git status
Decisions: P2 may close only as a generic protocol-definition phase; no concrete upstream adapter may claim conformance until its named downstream tests pass
Approval needed: none; documentation and local tests only
Secret/external-write status: no secrets handled; no cloud calls

Every agent must read this file, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, and `AGENTS.md` before changing product code.

## 2026-08-31 - P3-T01 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `4a1ad1a`
Scope: add the failing Herdr adapter availability test only
Upstream boundary: pinned Herdr v0.8.2 official binary discovery; socket/CLI health and real execution remain later tasks
Files intended: `tests/test_herdr_adapter.py`, tracker, handoff
Planned verification: targeted unittest must fail because `forma_ai.herdr_adapter` does not yet exist
Approval needed: none; no binary download or execution
Secret/external-write status: no secrets handled; no cloud calls

## 2026-08-31 - P3-T01 - exit

Executor: Codex root agent
Scope: failing test for official Herdr binary availability discovery
Actions: added deterministic missing-binary and discovered-only cases; both keep reachability and readiness false until a later real probe
Verification: `python3 -m unittest tests.test_herdr_adapter -v` failed as expected with `ModuleNotFoundError: No module named 'forma_ai.herdr_adapter'`
Files changed: `tests/test_herdr_adapter.py`, tracker, handoff
Commit: `6fc033b`
Push: pushed to `origin/main`
Decisions: executable discovery is availability evidence only and cannot satisfy Herdr health or execution acceptance
Blocked items: none
Next exact action: commit and push, then claim P3-T02
Approval needed: none
Secret/external-write status: no secrets handled; no cloud calls or Herdr execution

## 2026-08-31 - P3-T02 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `6fc033b`
Scope: minimal Herdr availability adapter skeleton
Files intended: `forma_ai/herdr_adapter.py`, tracker, handoff
Implementation boundary: injected executable discovery plus generic identity/health envelopes; no subprocess, socket, download, dispatch, or duplicate runtime logic
Planned verification: targeted Herdr tests, existing generic adapter-contract tests, and `git diff --check`
Approval needed: none
Secret/external-write status: no secrets handled; no cloud calls or Herdr execution

## 2026-08-31 - P3-T02 - exit

Executor: Codex root agent
Scope: minimal Herdr availability adapter skeleton
Actions: added injected official-binary discovery and generic identity/health envelopes; missing and discovered-only states remain explicitly unready
Verification: `python3 -m unittest tests.test_herdr_adapter tests.test_adapter_contract tests.test_agent_adapter_contract -v` passed 11 tests; `git diff --check` passed
Files changed: `forma_ai/herdr_adapter.py`, tracker, handoff
Commit: `5b4584d` plus this closeout record
Push: `5b4584d` pushed to `origin/main`; this closeout record is pushed in its follow-up commit
Decisions: no health probe, dispatch API, socket client, binary acquisition, or runtime duplication belongs in this skeleton
Blocked items: none
Next exact action: commit and push, then P3-T03
Approval needed: none
Secret/external-write status: no secrets handled; no cloud calls or Herdr execution

## 2026-08-31 - P0-T09 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `6fac496`
Scope: create two user-approved Chinese control-document mirrors in MyNote and enforce future bilingual synchronization
English authoritative files: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Chinese mirror folder: `/Users/rouice/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyNote/00_资源库/11_项目开发/Forma AI`
Files intended: `AGENTS.md`, both English control docs, and two Chinese Markdown mirrors
Planned verification: file existence, task/state/next-action parity, required sync-rule anchors, `git diff --check`, and repository cleanliness after commit/push
Approval: user explicitly approved writing the two mirrors to the named MyNote folder
Secret/external-write status: no secrets; authorized local MyNote writes only

## 2026-08-31 - P0-T09 - exit

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `6fac496`
Scope: create two Chinese MyNote control-document mirrors and enforce future bilingual synchronization
Actions: created a Chinese granular progress tracker and Chinese task handoff; added their exact paths and same-task parity gate to `AGENTS.md`, the English plan, and the English handoff
Verification: both external files exist; `P0-T09`, `P3-T03`, current-state, next-action, synchronization, and parity anchors were found; `git diff --check` passed
Files changed: `AGENTS.md`, both English control docs, and two authorized MyNote Chinese mirrors
Commit: `66434ff` plus this closeout record
Push: `66434ff` pushed to `origin/main`; this closeout record is pushed in its follow-up commit
Decisions: English repository documents remain authoritative for Git and machine execution; Chinese documents are mandatory equivalent operational mirrors, and mismatch blocks new work
Blocked items: none
Next exact action: commit and push, backfill the real commit into all four documents, then claim P3-T03 in both language sets
Approval: user explicitly approved the MyNote destination
Secret/external-write status: no secrets; only the approved local MyNote writes occurred

P0-T09 post-closeout index note: the two Chinese Markdown files are present and synchronized, but the optional GBrain refresh was not executed because `/Users/rouice/Gbrain/scripts/daily-growth/preflight.sh` failed its existing health gate with 2584 stale chunks not embedded. This is an indexing-health blocker, not a file-write or document-parity failure. Repair the GBrain stale-chunk condition before attempting refresh; do not rerun refresh past a failed preflight.

## 2026-08-31 - P3-T03 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `ce8a1dd`
Scope: add the failing test for two mock Herdr task starts with stable IDs and observable states
Upstream boundary: mock the official Herdr request boundary only; do not start a real process or invent an alternate scheduler
Files intended: `tests/test_herdr_adapter.py`, English and Chinese control documents
Planned verification: targeted unittest must fail on the missing spawn/status adapter surface
Approval needed: none; no Herdr process, cloud call, or credential use
Secret/external-write status: no secrets; only mandatory Chinese control-document synchronization

## 2026-08-31 - P3-T03 - exit

Executor: Codex root agent
Scope: two-mock-task Herdr spawn/status red test
Actions: required two `agent.start` calls, stable product/run/pane identities, two independent `agent.get` reads, running state, and monotonic revision evidence
Verification: `python3 -m unittest tests.test_herdr_adapter -v` kept 2 availability tests green and failed the new test as expected with `TypeError: HerdrAdapter.__init__() got an unexpected keyword argument 'request'`
Files changed: `tests/test_herdr_adapter.py`, English and Chinese control documents
Commit: `e652ed2`
Push: pushed to `origin/main`
Decisions: the adapter may translate the official request boundary but may not create a competing scheduler or claim real parallel execution from mocks
Blocked items: none
Next exact action: commit and push, then P3-T04
Approval needed: none
Secret/external-write status: no secrets; no Herdr process or cloud call

## 2026-08-31 - P3-T04 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `e652ed2`
Scope: minimal mockable Herdr task spawn/status mapping
Implementation boundary: injected request callable, immutable task envelope, official `agent.start` and `agent.get` translation only
Files intended: `forma_ai/herdr_adapter.py`, English and Chinese control documents
Planned verification: all Herdr adapter tests plus generic adapter-contract tests and `git diff --check`
Approval needed: none; no real Herdr or cloud execution
Secret/external-write status: no secrets; mandatory Chinese sync only

## 2026-08-31 - P3-T04 - exit

Executor: Codex root agent
Scope: minimal mockable Herdr spawn/status mapping
Actions: added immutable task envelope, injected request boundary, `agent.start` translation, `agent.get` status translation, and run-to-product-task correlation only
Verification: `python3 -m unittest tests.test_herdr_adapter tests.test_adapter_contract tests.test_agent_adapter_contract -v` passed 12 tests; `git diff --check` passed
Files changed: `forma_ai/herdr_adapter.py`, English and Chinese control documents
Commit: `2d56064`; subsequently corrected by `e6c4106`
Push: both commits pushed to `origin/main`
Decisions: Herdr responses remain authoritative; the local run/task correlation is not a scheduler or lifecycle state machine
Blocked items: none
Next exact action: commit and push, then P3-T05
Approval needed: none
Secret/external-write status: no secrets; no real Herdr or cloud execution

## 2026-08-31 - P3-T05 - takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `2d56064`
Scope: failing graceful-cancel and native-session-resume envelope tests
Pinned upstream facts: protocol 20 schema exposes `pane.send_keys`, `pane.close`, `pane.report_agent_session`, and `agent.start`; no high-level `agent.cancel` exists
Safety boundary: graceful cancel targets the exact known pane with `ctrl+c`; force close remains a separately approved future path; resume requires an authoritative native session reference and expected revision
Files intended: `tests/test_herdr_adapter.py`, English and Chinese control documents
Planned verification: existing tests stay green and new tests fail on missing lifecycle methods
Approval needed: none; mocks only
Secret/external-write status: no secrets; no real Herdr or cloud execution

## 2026-08-31 - P3-T04 - corrective takeover

Executor: Codex root agent
Trigger: pinned Herdr v0.8.2 protocol 20 schema disproved the first green mock contract
Incorrect assumption being removed: `agent.start` does not accept Forma task/correlation/working-directory fields and does not return a Forma run envelope
Verified upstream shape: `AgentStartParams` requires `name`, `kind`, and `pane_id`; success is `agent_started` containing `agent` and `argv`; `agent.get` success is `agent_info` containing `agent`
Correction boundary: product task/correlation/worktree data remains Forma-owned metadata; adapter maps upstream `AgentInfo` to a product run ID derived from task ID while preserving upstream pane/workspace/revision authority
Next exact action: correct tests first, observe failure against old implementation, then correct implementation and rerun the protocol suite
Approval needed: none; mocks and documentation only

## 2026-08-31 - P3-T04 - corrective exit

Executor: Codex root agent
Scope: repair the initial mock mapping to pinned Herdr v0.8.2 protocol 20
Actions: changed the red test to exact `AgentStartParams` and wrapped success shapes; observed expected old-implementation failure; corrected adapter to send only `name/kind/pane_id`, parse `agent_started.agent`, query `agent.get` by `target`, and parse `agent_info.agent`
Verification: corrected red test failed first on missing `agent_name`; after implementation, 12 Herdr and generic protocol tests passed and `git diff --check` passed
Files changed: `tests/test_herdr_adapter.py`, `forma_ai/herdr_adapter.py`, English and Chinese control documents
Commit: `e6c4106`
Push: pushed to `origin/main`
Decisions: Forma task/correlation metadata is not injected into Herdr schema; deterministic Forma run ID correlates the product task to the authoritative pane
Blocked items: none
Next exact action: commit/push correction, then P3-T05
Approval needed: none
Secret/external-write status: no secrets; mocks only

## 2026-08-31 - P3-T05 - resumed takeover

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `e6c4106`
Scope: resume lifecycle red tests on the corrected protocol 20 mapping
Test boundary: exact-pane graceful interrupt through `pane.send_keys`; native resume must first reconcile `agent.get` session reference and revision, then call schema-valid `agent.start`
Next exact action: add tests and preserve expected missing-method failures
Approval needed: none; mocks only

## 2026-08-31 - P3-T05 - exit

Executor: Codex root agent
Scope: lifecycle red tests on corrected Herdr protocol 20 mapping
Actions: added exact-pane graceful interrupt test using `pane.send_keys` and native resume test requiring `agent.get` session/revision reconciliation before schema-valid `agent.start`
Verification: `python3 -m unittest tests.test_herdr_adapter -v` passed 3 existing tests and failed 2 new tests as expected with missing `cancel_task` and `resume_task`
Files changed: `tests/test_herdr_adapter.py`, English and Chinese control documents
Commit: `db9c0ee` plus this closeout record
Push: `db9c0ee` pushed to `origin/main`; this closeout record is pushed in its follow-up commit
Decisions: no fictional `agent.cancel`; no native session field is sent in `AgentStartParams`; force close remains separately approval-gated
Blocked items: none
Next exact action: commit and push, then P3-T06
Approval needed: none
Secret/external-write status: no secrets; mocks only

## 2026-08-31 - P3-T06 - takeover

Executor: Codex root agent
Starting git state: clean at `5fe31d0` after fast-forwarding P4-T01; `origin/main` synchronized at takeover
Recovered breakpoint: P3-T05 red tests committed/pushed as `db9c0ee`; P3 batch closeout `8e09942`; P3-T06 was pending
Parallel boundary: P4-T02 is owned by the dedicated workbench task; this task changes only P3 lifecycle mapping and shared control records
Scope: implement graceful cancel and native-session resume mappings
Implementation boundary: exact cached pane target; `pane.send_keys` with `ctrl+c`; no force close; reconcile `agent.get` session and revision before schema-valid `agent.start`
Files intended: `forma_ai/herdr_adapter.py`, English and Chinese control documents
Planned verification: Herdr adapter tests, generic adapter-contract tests, `git diff --check`, then commit/push after integrating any newer P4 origin commits
Approval needed: none; mocks only
Secret/external-write status: no secrets; mandatory Chinese control-document synchronization only

## 2026-08-31 - P3-T06 - exit

Executor: Codex root agent
Recovered breakpoint: P3-T05 red tests at `db9c0ee`, P3 batch closeout at `8e09942`, P3-T06 pending; P4-T01 was fast-forwarded through `5fe31d0` before implementation
Scope: minimal Herdr graceful-cancel/native-session-resume mapping
Actions: added immutable lifecycle result; exact cached-pane `pane.send_keys` with `ctrl+c`; revision conflict rejection; full native session reference reconciliation through `agent.get`; schema-valid `agent.start` only after reconciliation
Verification: `python3 -m unittest tests.test_herdr_adapter tests.test_adapter_contract tests.test_agent_adapter_contract -v` passed 14 tests; after rebasing onto P4-T02, `swift test --package-path prototypes/packaging` passed 31 tests with 2 real-Keychain skips; `git diff --check` passed
Files changed: `forma_ai/herdr_adapter.py`, English and Chinese control documents
Commit: rebased after P4-T03 as implementation `9616aa1`, closeout `2fdd62b`, plus this final sync record
Push: pending final sync push
Decisions: force close is not implemented; session or revision drift fails closed; Herdr pane/agent responses remain authoritative
Blocked items: none
Next exact action: synchronize Chinese exit, recheck origin, commit/rebase if needed, push, then P3-T07
Approval needed: none
Secret/external-write status: no secrets; mocks only

## Handoff Rules

- Claim exactly one task ID from the master plan before editing.
- Update the master plan and this handoff before ending a turn, even if the task is blocked.
- Never mark work complete without commands, test output, artifact evidence, or an explicit reason why verification was impossible.
- Preserve unrelated dirty work. Do not revert or overwrite changes made by another agent or by the user.
- Do not write secrets, API keys, full prompts containing credentials, or private account data into this file.
- For cloud providers, record provider name, policy decision, approximate cost boundary, result class, and correlation ID if available. Do not record keys.
- For screenshots, record what the screenshot actually proves. Do not treat a wrong-window or background capture as UI evidence.
- If an external agent, tool, or parallel task takes over, it must add a takeover entry before work and an exit entry after work.
- The two Chinese mirrors in the user-approved MyNote `00_资源库/11_项目开发/Forma AI` folder must receive the equivalent baton and progress update during the same takeover/exit. The English repository documents remain authoritative; a parity mismatch must be repaired before product work resumes.
- A Codex quota warning triggers immediate closeout: start no new work, verify the smallest safe unit, update tracker and handoff, commit and push, and confirm repository cleanliness. Never discard unrelated dirty work merely to make status clean; inventory and isolate it instead.

## Current Baton

Updated: 2026-09-01 Asia/Shanghai
Owner: Codex root agent
Master plan task: P4-T14
State: P4-T13 verified; P4-T14 pending
Next required action: claim P4-T14 and build bilingual governed-memory review Preview surfaces.

## Product Goal Snapshot

The product is a local-first, multi-agent Mac AI workbench.

- Product-owned native workbench is the default distributable UI.
- holaOS is a capability/workflow reference and optional separately installed adapter until redistribution is cleared.
- Herdr is the core multi-agent runtime and must support parallel execution, readable state, cancellation, resume, and recovery.
- Semantica is the governed long-term memory and decision-evidence authority.
- oMLX is the local inference runtime and must prove real inference.
- Cloud models are optional, explicit, credential-gated, approval-gated, and audited.

## Current Worktree Fact

After P4-T12C implementation, `main` and `origin/main` contain verified commit `c003459`; the remaining closeout-only control update is owned by the current agent. There are no uncommitted paths assigned to another owner.
After P4-T13 implementation, `main` and `origin/main` contain verified commit `5a06fea`; the remaining closeout-only control update is owned by the current agent. There are no uncommitted paths assigned to another owner.

## Historical Interrupted Paths

The following paths appeared in an earlier dirty-worktree handoff. They are retained only as historical recovery context and must not be treated as currently dirty, currently owned, or currently verified:

- `forma_ai/deepseek_adapter.py`
- `tests/test_deepseek_adapter.py`
- `prototypes/packaging/Sources/LifecycleContract/ProductManifest.swift`
- `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift`
- `prototypes/packaging/Tests/LifecycleContractTests/ProductManifestTests.swift`
- `build/`
- `evidence/ui/cloud-settings-review-2026-08-31.png`

Before resuming related work, inspect the current file and Git history, claim the applicable master-plan task, and revalidate behavior. Do not infer present changes from this historical list.

## Interrupted Work Summary

DeepSeek/cloud setup work was in progress before this handoff:

- Dedicated DeepSeek credentials were configured by the user in the project.
- The conversation UI still did not provide a usable task/chat experience.
- The DeepSeek adapter had uncommitted changes around urllib opener timeout handling and unexpected error classification.
- A real DeepSeek attempt reached the provider but ended as `DEEPSEEK_RESPONSE_INVALID`.
- The likely hypothesis was an output-budget/thinking-mode interaction, but that is not verified.
- A true low-cost DeepSeek closed loop remains open under master-plan task P5-T04.

Settings/workbench work was in progress before this handoff:

- Cloud settings were being moved toward a clearer product settings flow.
- User feedback shows the current Settings & Recovery page behaves like initialization/recovery, not like a full product settings surface.
- The current visible product shape is insufficient: New task, History, and Settings & Recovery do not yet explain or deliver the target workbench.
- Future UI work must make the first screen a usable multi-agent task workbench, not a diagnostic panel.

Previously reported local verification that must be revalidated before relying on it:

- `swift test --package-path prototypes/packaging`: 30 passed, 2 skipped.
- Targeted Python DeepSeek/Supervisor tests: 43 passed.
- `evidence/ui/cloud-settings-review-2026-08-31.png` did not prove the foreground app state and must not be treated as acceptance evidence.

## Takeover Checklist

1. Read `AGENTS.md`.
2. Read `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`.
3. Read this file.
4. Inspect current git status.
5. Choose the next `pending` task from the master plan unless the user gives a different task.
6. Change that task to `in_progress` in the master plan.
7. Add a takeover entry here.
8. Do the smallest verifiable unit of work.
9. Run the listed verification.
10. Update both documents with result, evidence, commit status, and next action.

## Entry Template

```text
## YYYY-MM-DD HH:mm Asia/Shanghai - TASK-ID - takeover|exit

Executor:
Starting git state:
Scope:
Files intended:
Actions:
Verification:
Evidence:
Files changed:
Commit:
Push:
Decisions:
Assumptions:
Blocked items:
Next exact action:
Approval needed:
Secret/external-write status:
Quota state and closeout action:
```

## Handoff Log

## 2026-08-31 - P2-T07 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `026e9da`
Scope: specify a vendor-neutral AI-agent adapter for Codex, Claude, and compatible terminal/API tools
Files intended: contract document, contract tests, master tracker, and handoff
Actions: defined normative discover/dispatch/status/handoff/cancel/resume/artifacts/audit operations; fixed Herdr execution authority, reconnect/revision/idempotency behavior, secret/policy/audit boundaries, and minimum conformance evidence
Verification: `python3 -m unittest tests.test_agent_adapter_contract tests.test_adapter_contract -v` passed 9 tests; `git diff --check` passed
Evidence: contract document plus machine checks for all operations, runtime/memory authority, cancellation/recovery, approval/audit, artifacts, and parallel-run conformance
Files changed: `docs/contracts/agent-adapter.md`, `tests/test_agent_adapter_contract.py`, master tracker, and handoff
Commit: `2b5227c` (`docs: specify universal agent adapter contract`)
Push: pushed to `origin/main`; branch synchronized
Decisions: adapter implementations translate to Herdr rather than replacing it; unknown/disconnected/blocked states never become success; force cancellation and external writes remain approval-gated
Assumptions: concrete Codex/Claude adapters will prove this same contract in later implementation tasks
Blocked items: none for specification; concrete runtime conformance remains later work
Next exact action: claim P2-T08 and audit/close P2
Approval needed: none
Secret/external-write status: no secrets; repository-local docs/tests only
Quota state and closeout action: no warning; verified contract unit ready to push

## 2026-08-31 - P2-T07 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `026e9da`
Scope: specify a vendor-neutral AI-agent adapter for Codex, Claude, and compatible terminal/API tools
Files intended: `docs/contracts/agent-adapter.md`, contract tests, master tracker, and handoff
Actions: claimed P2-T07 in plan order
Verification: pending contract validation test
Evidence: Herdr v0.8.2 capability ledger, holaOS harness map, and P2 identity/capability/policy/audit envelopes
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: contract covers discover, dispatch, status, handoff, cancel, resume, artifacts, audit and reconnect semantics; Herdr remains execution authority
Assumptions: document requirements can be machine-checked before concrete adapter implementations exist
Blocked items: none
Next exact action: inspect contract/test layout, create the specification and its validation test, then run it
Approval needed: none
Secret/external-write status: no secrets; repository-local docs/tests only
Quota state and closeout action: no warning; close and push current unit on warning

## 2026-08-31 - P2-T06 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `69a21cc`
Scope: implement only the policy-preview and audit envelopes required by P2-T05
Files intended: adapter contract, master tracker, and handoff
Actions: added immutable `PolicyPreview` and `AuditEnvelope` with deterministic JSON-compatible serialization and no raw payload field
Verification: adapter contract suite passed 5 tests; `git diff --check` passed
Evidence: targeted unittest output
Files changed: adapter contract, master tracker, and handoff
Commit: pending implementation commit
Push: pending
Decisions: policy preview binds digest and approval boundary; audit records only correlation/action/outcome/time/redaction metadata
Assumptions: stricter value validation can be introduced by a later explicit contract revision
Blocked items: none
Next exact action: commit/push P2-T06, then claim P2-T07
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; verified unit ready to push

## 2026-08-31 - P2-T06 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `69a21cc`
Scope: implement only the policy-preview and audit envelopes required by P2-T05
Files intended: adapter contract, master tracker, and handoff
Actions: claimed P2-T06 in plan order
Verification: pending targeted unittest
Evidence: P2-T05 red tests
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: immutable envelopes and explicit tuple-to-list serialization; no raw payload content field
Assumptions: field validation remains outside this minimal planned slice
Blocked items: none
Next exact action: add the two dataclasses and run contract tests
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; close and push current unit on warning

## 2026-08-31 - P2-T05 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `a012fcd`
Scope: define intentionally failing policy-preview and audit-envelope contract tests
Files intended: test, master tracker, and handoff
Actions: added exact payload digest/data-class/external-write/approval preview contract and correlated outcome/timestamp/redacted-field audit contract; added no implementation
Verification: targeted unittest failed at intended boundary with missing `AuditEnvelope` import; `PolicyPreview` is also intentionally absent
Evidence: unittest output and two red tests
Files changed: test, master tracker, and handoff
Commit: pending red-test commit
Push: pending
Decisions: raw payload, prompt, and credential values are absent from the audit envelope by construction
Assumptions: tuple fields serialize as ordered JSON lists
Blocked items: none; failure intentional
Next exact action: commit/push P2-T05, then claim P2-T06
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; red unit ready to push

## 2026-08-31 - P2-T05 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `a012fcd`
Scope: define intentionally failing policy-preview and audit-envelope contract tests
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T05 in plan order and reconciled the prior baton with pushed P2-T04
Verification: pending expected failing unittest
Evidence: product approval/audit rules and existing cloud proposal/audit implementations
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: preview binds exact payload digest, data classes, external-write and approval state; audit stores correlation/action/outcome/timestamp and names redacted fields without payload content
Assumptions: event and correlation IDs remain opaque in this minimal contract slice
Blocked items: none
Next exact action: add red tests and capture the missing-symbol failure
Approval needed: none
Secret/external-write status: no secrets; repository-local tests only
Quota state and closeout action: no warning; close and push current red unit on warning

## 2026-08-31 - P2-T04 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `61b4aef`
Scope: implement only the capability declaration required by P2-T03
Files intended: adapter contract, master tracker, and handoff
Actions: added immutable `CapabilityDeclaration`; converted tuple operations to an ordered JSON-compatible list
Verification: targeted adapter contract suite passed 3 tests; `git diff --check` passed
Evidence: unittest output
Files changed: `forma_ai/adapter_contract.py`, master tracker, and handoff
Commit: pending implementation commit
Push: pending
Decisions: declarations report capability evidence but do not assert successful runtime execution
Assumptions: validation constraints will be introduced only through later explicit tests
Blocked items: none
Next exact action: commit/push P2-T04, then claim P2-T05
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; verified unit ready to push

## 2026-08-31 - P2-T04 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `61b4aef`
Scope: implement only the capability declaration required by P2-T03
Files intended: `forma_ai/adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T04 in plan order
Verification: pending targeted unittest
Evidence: P2-T03 expected missing-symbol failure
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: immutable declaration; tuple operations serialize to a JSON-compatible ordered list
Assumptions: field validation remains outside this planned minimal slice
Blocked items: none
Next exact action: implement the dataclass and run the adapter contract tests
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; close and push on warning

## 2026-08-31 - P2-T03 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `947268d`
Scope: define the intentionally failing capability-declaration contract test
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: added a vendor-neutral `agent_execution` declaration requiring deterministic `dispatch`, `status`, `cancel`, and `resume` operations plus proof level; added no implementation
Verification: targeted unittest failed at the intended boundary: `ImportError: cannot import name 'CapabilityDeclaration'`
Evidence: unittest output and test contract
Files changed: test, master tracker, and handoff
Commit: pending red-test commit
Push: pending
Decisions: declaration reports supported operations and evidence; it does not imply runtime success
Assumptions: tuple order is retained in serialized output
Blocked items: none; failure is intentional
Next exact action: commit/push P2-T03, then claim P2-T04
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; red-test unit ready to push

## 2026-08-31 - P2-T03 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `947268d`
Scope: define the intentionally failing capability-declaration contract test
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T03 in plan order and reconciled the prior baton with the already pushed P2-T02 commit
Verification: pending expected failing unittest result
Evidence: P2-T01/T02 identity and health contract plus upstream capability ledgers
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: capability declaration is vendor-neutral and names stable operations plus evidence level; implementation belongs only to P2-T04
Assumptions: operation order is part of deterministic serialized output for this minimal slice
Blocked items: none
Next exact action: add the test and capture the expected missing-symbol failure
Approval needed: none
Secret/external-write status: no secrets; repository-local test only
Quota state and closeout action: no warning; close and push this red-test unit if a warning appears

## 2026-08-31 - P2-T02 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `0df9d25`
Scope: implement only the adapter identity and health-envelope dataclasses required by P2-T01
Files intended: `forma_ai/adapter_contract.py`, master tracker, and handoff
Actions: added immutable `AdapterIdentity` and `HealthEnvelope` dataclasses with deterministic `to_dict` serialization; added no capability or policy surface
Verification: `python3 -m unittest tests.test_adapter_contract -v` passed 2 tests; `git diff --check` passed
Evidence: targeted unittest output
Files changed: `forma_ai/adapter_contract.py`, master tracker, and this handoff
Commit: pending implementation commit
Push: pending
Decisions: minimal implementation preserves the red-test boundary and defers validation/capability/policy behavior to their planned tests
Assumptions: opaque strings are sufficient for the current contract slice
Blocked items: none
Next exact action: commit/push P2-T02, then claim P2-T03
Approval needed: none
Secret/external-write status: no secrets; repository-local code and tests only
Quota state and closeout action: normal; verified unit is ready to commit and push

## 2026-08-31 - P2-T02 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `0df9d25`
Scope: implement only the adapter identity and health-envelope dataclasses required by P2-T01
Files intended: `forma_ai/adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T02 in plan order
Verification: pending targeted unittest
Evidence: P2-T01 red test
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: immutable dataclasses with deterministic dictionary serialization; no capability or policy fields before their own red tests
Assumptions: current string fields remain opaque contract values until later validation tasks require constraints
Blocked items: none
Next exact action: add the minimal module and run `tests.test_adapter_contract`
Approval needed: none
Secret/external-write status: no secrets; repository-local code and tests only
Quota state and closeout action: normal; close and push this implementation unit on warning

## 2026-08-31 - P2-T01 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `f3cd94e`
Scope: add the first intentionally failing contract test for adapter identity and health envelope
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: defined exact stable identity fields and a health envelope that separates reachability, readiness, proof level, timestamp, and reason code; did not add implementation
Verification: `python3 -m unittest tests.test_adapter_contract -v` failed at the intended boundary with `ModuleNotFoundError: No module named 'forma_ai.adapter_contract'`
Evidence: unittest output and the new two-test contract file
Files changed: `tests/test_adapter_contract.py`, master tracker, and this handoff
Commit: pending red-test commit
Push: pending
Decisions: identity is vendor-neutral and versioned; health cannot collapse reachable, ready, and real proof into one boolean
Assumptions: P2-T02 will implement only the surface demanded by these tests
Blocked items: none; failure is intentional and required by the plan
Next exact action: commit/push P2-T01, then claim P2-T02
Approval needed: none
Secret/external-write status: no secrets; repository-local test only
Quota state and closeout action: normal; red-test unit is ready to commit and push

## 2026-08-31 - P2-T01 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `f3cd94e`
Scope: add the first intentionally failing contract test for adapter identity and health envelope
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T01 in plan order
Verification: pending expected failing unittest result
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: test only stable vendor-neutral identity and health fields; implementation belongs to P2-T02 and must not be added in this task
Assumptions: an import failure is too coarse; the test should import a named contract surface and then fail because that module is absent
Blocked items: none
Next exact action: inspect local test conventions, create the minimal contract test, and capture the expected failure
Approval needed: none
Secret/external-write status: no secrets; repository-local test only
Quota state and closeout action: normal; close and push this test unit on warning

## 2026-08-31 - P1-T08 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `0de31a5`
Scope: audit and close the complete P1 upstream inventory documentation chain
Files intended: master tracker and handoff only
Actions: verified P1-T01 through P1-T07 status, required evidence files, four decision records, seven scoped commits, origin/main synchronization, whitespace, and pre-close repository state
Verification: all four research/evidence files exist; exactly four reuse decisions exist; no P1-T01 through P1-T07 task remains pending/in-progress/blocked; `git log` shows commits `b799a63`, `64bb3a9`, `fcf9308`, `85f7e54`, `7e42050`, `a7062e5`, and `0de31a5`; `origin/main...HEAD` was empty; `git diff --check` passed
Evidence: repository files, master tracker, decision log, local Git history, and remote-tracking comparison
Files changed: master tracker and this handoff
Commit: pending phase-close documentation commit
Push: pending
Decisions: individual scoped commits satisfy the inventory commit requirement and preserve reviewable history; P1 exit gate is met
Assumptions: remote-tracking `origin/main` reflects the successful push immediately preceding this audit
Blocked items: none
Next exact action: commit/push P1 closeout, then claim P2-T01
Approval needed: none
Secret/external-write status: no secrets; Git push only
Quota state and closeout action: normal; phase closeout is ready to commit and push

## 2026-08-31 - P1-T08 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `0de31a5`
Scope: audit and close the complete P1 upstream inventory documentation chain
Files intended: master tracker and handoff only if the existing inventory commits and evidence pass
Actions: claimed P1-T08 in plan order
Verification: pending status/file/history/push/cleanliness audit
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: P1 closes only if P1-T01 through P1-T07 are verified, evidence files exist, commits contain scoped documentation, and origin/main contains the chain
Assumptions: individual verified task commits satisfy the P1-T08 inventory commit intent; this task records the aggregate audit rather than squashing history
Blocked items: none
Next exact action: run aggregate P1 evidence, history, remote, and cleanliness checks
Approval needed: none
Secret/external-write status: no secrets; repository-local and Git metadata checks only
Quota state and closeout action: normal; close and push this phase audit on warning

## 2026-08-31 - P1-T07 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `a7062e5`
Scope: record durable, evidence-linked reuse decisions for Semantica, holaOS, Herdr, and oMLX
Files intended: decision log, master tracker, and handoff
Actions: added one explicit record per upstream naming its pinned revision, integration mode, Forma-owned boundary, forbidden duplication, acceptance evidence, and distribution obligations
Verification: exactly four `Reuse decision` records exist; all four upstreams and required boundary/acceptance/public terms are present; `git diff --check` passed
Evidence: P1 capability ledgers, upstream matrix, runbook, and license matrix
Files changed: `docs/decisions.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: these four records operationalize ADR-017 and cannot be overridden by older superseded summaries
Assumptions: exact upstream revisions will be re-reviewed before any later upgrade
Blocked items: none for decision recording; implementation acceptance remains in later phases
Next exact action: commit/push P1-T07, then claim P1-T08
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T07 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `a7062e5`
Scope: record durable, evidence-linked reuse decisions for Semantica, holaOS, Herdr, and oMLX
Files intended: `docs/decisions.md`, master tracker, and handoff
Actions: claimed P1-T07 in plan order
Verification: pending four-decision scan and conflict check
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: each record must name the selected integration mode, product-owned boundary, forbidden duplication, validation gate, and distribution consequence
Assumptions: existing superseded ADR summaries remain historical but cannot override the new records
Blocked items: none
Next exact action: inspect the decision log and add four explicit reuse decisions linked to the P1 ledgers
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T06 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `7e42050`
Scope: reconcile Semantica, holaOS, Herdr, and oMLX license obligations with personal development and future public open-source distribution
Files intended: license matrix, master tracker, and handoff
Actions: bound each component to its reviewed revision; separated private, public-source, copied-source, binary, adapter, and commercial modes; added provenance, notices, SBOM, trademark, asset, model, and dependency gates
Verification: required public/redistribution/holaOS terms plus all reviewed revisions and release-mode gates are present; `git diff --check` passed
Evidence: P1-T02 through P1-T05 upstream ledgers and commit-pinned official license links
Files changed: `docs/research/license-matrix.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: open source and non-commercial are not interchangeable; public Forma source without copied upstream code is the lowest-risk candidate; holaOS frontend/bundling remains blocked without written clearance
Assumptions: matrix is engineering compliance guidance, not legal advice
Blocked items: file-level provenance, third-party notices, SBOM, transitive/model licenses, and written holaOS clarification remain P8 release gates
Next exact action: commit/push P1-T06, then claim P1-T07
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T06 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `7e42050`
Scope: reconcile Semantica, holaOS, Herdr, and oMLX license obligations with personal development and future public open-source distribution
Files intended: `docs/research/license-matrix.md`, master tracker, and handoff
Actions: claimed P1-T06 in plan order
Verification: pending matrix and upstream-ledger conflict scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: public source publication, binary distribution, commercial distribution, trademarks/assets, and separately installed adapters must be treated as distinct release modes
Assumptions: this is an engineering compliance gate, not legal advice
Blocked items: none
Next exact action: inspect and reconcile the license matrix with the pinned upstream evidence already recorded in P1-T02 through P1-T05
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T05 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `85f7e54`
Scope: refresh oMLX v0.6.3 API, runtime, model, release, inference-proof, and adapter-boundary evidence
Files intended: upstream matrix, oMLX runbook, master tracker, and handoff
Actions: resolved the lightweight tag; reviewed official release assets/digests, pinned server routes and package dependencies; reconciled local adapter, broker, manifest, generation, and embedding evidence; corrected the stale runbook statement that deep inference was wholly unverified
Verification: `python3 -m unittest tests.test_omlx_adapter tests.test_manifest -v` passed 24 tests; required commit, artifact digest, API routes, chat proof, embedding boundary, pending gates, and health-contract terms are present; `git diff --check` passed
Evidence: official `jundot/omlx` v0.6.3 tag/release API and pinned `server.py`/`pyproject.toml`; repository generation, embedding, isolation/broker evidence and current adapter/manifest tests
Files changed: `docs/research/upstream-matrix.md`, `docs/runbooks/omlx.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: chat generation is verified only for the exact pinned oMLX/Qwen pair; route availability does not grant model capability; embedding, streaming, cancellation, pressure, sustained concurrency, restart, updater, and complete isolation remain open
Assumptions: prior terminal evidence is valid repository evidence but does not substitute for future native user-flow acceptance
Blocked items: no approved embedding model; no new real-runtime execution was required for this inventory correction
Next exact action: commit/push P1-T05, then claim P1-T06
Approval needed: none
Secret/external-write status: no secrets; public read-only source access and local tests only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T05 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `85f7e54`
Scope: refresh oMLX v0.6.3 API, runtime, model, release, inference-proof, and adapter-boundary evidence
Files intended: `docs/research/upstream-matrix.md`, master tracker, and handoff
Actions: claimed P1-T05 in plan order
Verification: pending official tag/source/API/release inspection and repository adapter scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: health and model listing remain readiness signals only; acceptance requires a real chat completion or embedding response tied to a model ID
Assumptions: exact v0.6.3 artifacts and source must be bound before compatibility claims
Blocked items: none
Next exact action: inspect official repository tag, release assets/digests, API routes and schemas, runtime requirements, and existing Forma integration code
Approval needed: none
Secret/external-write status: no secrets; public read-only source access and local read-only inspection only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T04 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `fcf9308`
Scope: map Herdr v0.8.2 CLI/socket capabilities, multi-agent lifecycle, source entry points, release artifacts, and license obligations
Files intended: `docs/research/herdr-capability-ledger.md`, master tracker, and handoff
Actions: resolved the annotated tag to its commit; reviewed immutable release assets/digests, Cargo manifest, Apache license, pinned source tree, bundled protocol schema, socket API, and session/recovery semantics
Verification: ledger exists; exact commit and macOS digest, snapshot/events, parallel dispatch, prompt/wait, state, cancel policy gap, native resume, restart recovery, handoff, security, source entry points, and validation gaps are present; `git diff --check` passed
Evidence: official `herdrdev/herdr` v0.8.2 tag/release API and commit-pinned README, Cargo manifest, LICENSE, recursive source tree, socket API, session-state documentation, and API schema
Files changed: `docs/research/herdr-capability-ledger.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: integrate the verified official binary through CLI and local socket; Herdr remains the mandatory runtime authority while Forma AI owns policy, orchestration intent, UI, and audit
Assumptions: upstream protocol surfaces remain unaccepted until the exact binary is downloaded, digest-verified, and exercised locally
Blocked items: no local runtime test yet; cancellation requires a Forma policy over pane/process controls because no single high-level `agent.cancel` appeared in the reviewed map
Next exact action: commit/push P1-T04, then claim P1-T05
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T04 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `fcf9308`
Scope: map Herdr v0.8.2 CLI/socket capabilities, multi-agent lifecycle, source entry points, release artifacts, and license obligations
Files intended: `docs/research/herdr-capability-ledger.md`, master tracker, and handoff
Actions: claimed P1-T04 in plan order
Verification: pending official tag/source/protocol/release/license inspection and ledger completeness scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: Herdr remains the required core execution runtime; the ledger must prevent cosmetic or product-owned replacement of upstream multi-agent lifecycle behavior
Assumptions: v0.8.2 must resolve to an immutable commit and artifacts before integration
Blocked items: none
Next exact action: inspect official repository metadata, tag, release assets, source tree, CLI/socket documentation, Cargo manifest, and license
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T03 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `64bb3a9`
Scope: map holaOS capabilities, source entry points, non-visual reuse candidates, visual/branding exclusions, and distribution obligations
Files intended: `docs/research/holaos-capability-ledger.md`, master tracker, and handoff
Actions: reviewed official commit, repository/workspace shape, runtime and package entry points, README claims, and modified license; recorded a granular upstream-first reuse boundary
Verification: ledger exists; required revision, runtime/package entry points, license/public-distribution boundary, Semantica memory authority, Herdr role, and open validation gaps are present; `git diff --check` passed
Evidence: official `holaboss-ai/holaOS` repository API and commit-pinned README, LICENSE, root manifest, runtime tree, and packages tree at `4684714ee133794cdbb86630e42b7d93447fb2e2`
Files changed: `docs/research/holaos-capability-ledger.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: reuse eligible non-visual runtime/client/SDK implementation behind adapters; exclude shared UI and branded desktop frontend; keep holaOS memory transient and Semantica authoritative
Assumptions: README capability descriptions require source-level and runtime validation before integration claims
Blocked items: no local pinned checkout/build; exact file-level MCP/provider/browser/integration/automation paths remain a later acquisition/compatibility gate
Next exact action: commit/push P1-T03, then claim P1-T04
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T03 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `64bb3a9`
Scope: map holaOS capabilities, source entry points, non-visual reuse candidates, visual/branding exclusions, and distribution obligations
Files intended: `docs/research/holaos-capability-ledger.md`, master tracker, and handoff
Actions: claimed P1-T03 in plan order
Verification: pending official source tree/package/license inspection and ledger completeness scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: maximize licensed non-visual reuse during personal non-commercial development while maintaining a separable public-distribution boundary
Assumptions: exact main commit must be recorded because `latest` is rolling
Blocked items: none
Next exact action: inspect official repository metadata, current main commit, package/workspace manifests, source tree, README, and LICENSE
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T02 - exit

Executor: Codex root agent
Starting git state: clean after `b799a63`
Scope: refresh Semantica v0.6.7 version, API, capability, packaging, storage, and reuse-boundary evidence
Files intended: upstream matrix, master tracker, and handoff
Actions: verified official v0.6.7 tag target, release assets/digests, Python manifest, entry points, dependency shape, AgentContext surface, and current Forma AI integration boundary
Verification: expected repository `rg` scan passed; matrix contains exact commit, asset digests, five entry points, upstream capability table, and product responsibility boundary; whitespace check passed
Evidence: official Semantica GitHub tag/release API, versioned `pyproject.toml`, pinned `AgentContext` source, Forma AI adapter/backend/runbook and ADR-0011
Files changed: `docs/research/upstream-matrix.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: directly reuse AgentContext and upstream decision/causal/provenance/graph/MCP capabilities; product-owned code remains governance, isolation, approval, audit, and UI integration only
Assumptions: unsigned tag and mutable release metadata require commit plus asset-digest binding
Blocked items: real managed Semantica runtime and production embedding approval remain later implementation gates, not blockers for inventory
Next exact action: commit/push P1-T02, then claim P1-T03
Approval needed: none
Secret/external-write status: no secrets; official public sources only
Quota state and closeout action: normal; independently verified unit ready to commit and push

## 2026-08-31 - P1-T02 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `b799a63`
Scope: refresh Semantica v0.6.7 API, capability, packaging, storage, and reuse-boundary evidence
Files intended: `docs/research/upstream-matrix.md`, master tracker, and handoff
Actions: claimed P1-T02 in plan order
Verification: pending official repository/tag/package inspection and repository boundary scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: Semantica remains the governed memory authority; reuse upstream APIs/packages rather than reconstructing memory primitives
Assumptions: versioned v0.6.7 evidence controls the current pin even if `main` has moved
Blocked items: none
Next exact action: inspect official v0.6.7 release, manifest, CLI/MCP/server/storage surfaces, and compare with Forma AI adapters
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T01 - exit

Executor: Codex root agent
Starting git state: clean at `5cee7a9`
Scope: inventory repository and bounded machine-local checkouts, pins, and installed artifacts for all four upstream foundations
Files intended: upstream matrix, master tracker, and handoff
Actions: scanned repository integrations, prior research workspace, normal Applications folders, and product-managed support paths; inspected the oMLX bundle and active artifact record; distinguished empty research directories from Git checkouts
Verification: repository file scan found Semantica/oMLX adapters only; no upstream Git checkout was found in the bounded search; Semantica-named research directory is not a Git repository; installed oMLX reports bundle ID `app.omlx`, version `0.6.3`, build `2500`, and the expected artifact digest
Evidence: updated `docs/research/upstream-matrix.md` local inventory table; `config/upstreams.json`; `config/product-manifest.json`; read-only oMLX Info.plist and active record
Files changed: `docs/research/upstream-matrix.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: installed oMLX is binary evidence, not source evidence; `latest` is not an acceptable holaOS pin; absence of local source never authorizes reimplementation
Assumptions: search is explicitly bounded and does not prove machine-wide absence
Blocked items: none for P1-T01
Next exact action: commit/push P1-T01, then claim P1-T02
Approval needed: none
Secret/external-write status: no secrets; no cloud calls
Quota state and closeout action: normal; task is independently committable and ready for quota-safe closeout

## 2026-08-31 - P1-T01 - takeover

Executor: Codex root agent
Starting git state: clean at `5cee7a9`; legacy build artifacts preserved in `stash@{0}`
Scope: list available local upstream checkouts, installed artifacts, declared pins, and gaps for all four foundations
Files intended: `docs/research/upstream-matrix.md`, master tracker, and this handoff
Actions: claimed P1-T01 after confirming the previous quota-safe closeout and reviewing the execution plan
Verification: pending repository file inventory and read-only local source discovery
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: inventory only; no upstream modification or new capability implementation
Assumptions: local checkouts outside the repository are read-only evidence and are not product dependencies until pinned and integrated
Blocked items: none
Next exact action: scan repository references, known development directories, installed application locations, and Git metadata for exact pins
Approval needed: none for read-only discovery
Secret/external-write status: no secrets; no cloud calls
Quota state and closeout action: normal; close current task immediately if a usage warning appears

## 2026-08-31 05:57 Asia/Shanghai - P0-T08 - exit

Executor: Codex root agent
Starting git state: quota-interrupted P0-T08 worktree plus preserved earlier DeepSeek/settings edits
Scope: resume at the exact interruption point, finish Forma AI global rename, icon contract test, validation, and quota-safe closeout
Files intended: all tracked product identity surfaces, Python module/import names, Swift targets, packaging identifiers, documentation, tests, and Forma AI icon assets
Actions: added missing automated icon assertions; confirmed product name/module/target/executable/environment/service/support-path migration; generated standard iconset and ICNS; integrated icon in Info.plist and app build; added the Codex quota exhaustion protocol
Verification: legacy-name scan outside preserved untracked historical build returned no match; full Python suite passed 225 with 1 skipped; targeted packaging suite passed 6; Swift suite passed 30 with 2 skipped; temporary signed `Forma AI.app` built successfully; Info.plist exposes `CFBundleName=Forma AI` and `CFBundleIconFile=FormaAI`; ICNS identified as a macOS icon; codesign verification passed; `git diff --check` passed
Evidence: `assets/branding/forma-ai-app-icon-1024.png`, `prototypes/packaging/Resources/FormaAI.icns`, temporary validation bundle `/tmp/forma-ai-validation-20260831-0203/Forma AI.app`
Files changed: tracked product source/tests/docs/config/packaging naming plus new branding and icon resources; earlier DeepSeek/settings edits are locally test-verified but the real DeepSeek closed loop remains pending under P5
Commit: `7068cba feat: rename product to Forma AI`; closeout commit `43ba7b1 docs: close Forma AI identity migration`
Push: commits through `43ba7b1` pushed to `origin/main`; final status record follows as documentation-only commit
Decisions: product and internal identity are Forma AI; no split legacy module/target/service identity remains in tracked files; generated build artifacts are not product source
Assumptions: pre-existing local DeepSeek/settings edits can be included because full Python and Swift suites pass, without claiming P5 real-provider acceptance
Blocked items: no P0-T08 blocker; real DeepSeek acceptance remains explicitly open
Next exact action: claim P1-T01 and inventory the four upstream checkouts/pins before new capability implementation
Approval needed: separate explicit approval remains required for a real DeepSeek call
Secret/external-write status: no project credential read or transmitted; only repository push remains
Quota state and closeout action: resumed after quota reset; completed and pushed the smallest verified unit; repository is clean; pre-existing untracked artifacts are preserved in `stash@{0}` named `pre-Forma legacy build artifacts and generated iconset 2026-08-31`

## 2026-08-31 - P0-T08 - takeover

Executor: Codex root agent
Starting git state: P0-T07 committed; earlier DeepSeek/settings source changes remain dirty and must be preserved through the mechanical rename
Scope: rename the product globally to Forma AI and add an original macOS application icon
Files intended: tracked source, tests, documentation, Swift package/targets, build scripts, product manifest, application metadata, and new icon assets
Actions: generated an original 1024px macOS icon concept using the built-in image generation workflow; inventoried tracked legacy names and identifiers
Verification: pending legacy-name absence scan, Python suite, Swift suite, and application bundle inspection
Evidence: generated source image at the Codex generated-image path; final project asset pending copy and iconset creation
Files changed: master tracker and handoff at takeover
Commit: P0-T07 commits `a618993` and `d190d90` complete; P0-T08 pending
Push: pending combined push
Decisions: public product name is `Forma AI`; internal module, target, executable, environment, support-directory, service, bundle, and documentation names will be migrated rather than leaving a split identity
Assumptions: historical evidence wording may be updated for product identity, while technical results and dates remain unchanged
Blocked items: none
Next exact action: perform mechanical rename, preserve dirty functional edits, create icon assets, update package metadata, and test
Approval needed: none for repository-local rename and generated asset integration
Secret/external-write status: no secrets handled; image generation only, no cloud model credential used from the project

## 2026-08-31 01:57 Asia/Shanghai - P0-T07 - exit

Executor: Codex root agent
Starting git state: dirty worktree with previously recorded DeepSeek/settings implementation changes
Scope: reconcile product-role documents and make upstream-first reuse enforceable
Files intended: governance, requirements, decisions, ADR-0017, active/legacy plans, license matrix, tracker, and handoff
Actions: corrected active role conflicts; marked the old plan superseded; made Herdr core; required licensed non-visual reuse from all four upstreams; separated personal non-commercial development from future public distribution; added universal Codex/Claude-compatible agent adapters and complete product Settings to requirements and the master plan
Verification: repository-wide role scan found no unmarked active conflict; `git diff --check` passed for all documentation files
Evidence: upstream-first implementation rule in `AGENTS.md`; ADR-003 superseded by ADR-017; ADR-0017 and product requirements require Herdr and upstream reuse; master plan contains CAP-11, CAP-12, P2-T07, and P4-T07
Files changed: `AGENTS.md`, `docs/decisions.md`, `docs/product-requirements.md`, `docs/adr/0017-product-owned-native-workbench.md`, both 2026-08-28 plans, license matrix, master tracker, and this handoff
Commit: `a618993 docs: enforce upstream-first product direction`; this closeout record follows in a documentation-only commit
Push: pending final closeout push
Decisions: independent visual workbench plus adapter protocol; reuse all license-permitted non-visual upstream capability; do not duplicate upstream functionality without recorded justification
Assumptions: personal non-commercial use does not waive license obligations; future public distribution requires a fresh exact-artifact review
Blocked items: none
Next exact action: commit and push documentation only, then claim P1-T01
Approval needed: none for documentation; cloud calls remain separately approval-gated
Secret/external-write status: no secrets handled; no cloud API calls

## 2026-08-31 - P0-T07 - takeover

Executor: Codex root agent
Starting git state: dirty worktree with the previously recorded DeepSeek/settings implementation changes
Scope: align active and legacy product documents with the confirmed independent-workbench, adapter-protocol, and upstream-first reuse target
Files intended: `AGENTS.md`, product requirements, decisions, ADR-0017, active/legacy plans, license matrix, master tracker, and this handoff
Actions: claimed P0-T07 after repository-wide conflict scan found documents that still called holaOS the default UI and Herdr optional
Verification: pending repository-wide role/reuse conflict scan and whitespace validation
Evidence: conflicts found in `docs/decisions.md`, `docs/product-requirements.md`, `docs/adr/0017-product-owned-native-workbench.md`, and `docs/plans/2026-08-28-forma-ai.md`
Files changed: master tracker and this handoff at takeover
Commit: none yet
Push: none yet
Decisions: reuse existing upstream functionality before product-owned implementation; new implementation is limited to the independent workbench, adapter/protocol/integration/policy gaps, license-blocked portions, or verified upstream capability gaps
Assumptions: non-commercial personal development does not waive license terms; public distribution remains a separate release gate
Blocked items: none
Next exact action: update conflicting documents, scan, verify, commit documentation only, and push
Approval needed: none for repository documentation edits
Secret/external-write status: no secrets handled; no cloud API calls

## 2026-08-31 - P0-T01 - takeover

Executor: Codex root agent
Starting git state: dirty worktree with DeepSeek/settings/test/build changes listed above
Scope: create execution-control documents and update `AGENTS.md`
Files intended: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`, `AGENTS.md`
Actions: started governance correction after user confirmed the need for granular tracking and handoff
Verification: `rg -n "Execution control documents|Task Handoff|Current Baton|P0-T01|Herdr is the core|holaOS is a capability"` found required anchors; `git diff --check -- AGENTS.md docs/plans/2026-08-31-multi-agent-workbench-master-plan.md docs/TASK_HANDOFF.md` passed
Evidence: `AGENTS.md` contains mandatory execution-control rules; master plan contains P0-P8 tracker; this file contains takeover protocol and current dirty-worktree baton
Files changed: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: `3756677 docs: add workbench execution control`
Push: governance documentation chain is pushed together with this final completion update
Decisions: product-owned independent workbench plus adapter protocol; holaOS capability parity without uncleared public bundling; Herdr core multi-agent runtime
Assumptions: documentation-control commit must not stage the interrupted implementation files
Blocked items: none for documentation-control task
Next exact action: claim P1-T01 or explicitly resume P5 DeepSeek work if the user chooses that path
Approval needed: none for documentation edits; separate approval still required for any cloud API call
Secret/external-write status: no secrets handled; no external cloud calls in this task

## 2026-08-31 - P0-T05 - exit

Executor: Codex root agent
Starting git state: dirty worktree with prior DeepSeek/settings changes preserved
Scope: commit governance documents only
Files intended: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Actions: staged only governance documents and committed them
Verification: `git diff --cached --name-only` listed only the three intended files before commit
Evidence: commit `3756677 docs: add workbench execution control`
Files changed: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: `3756677`
Push: pending
Decisions: completion evidence must be written back before push closeout
Assumptions: second documentation commit is acceptable to avoid self-referential commit metadata
Blocked items: none
Next exact action: commit this completion-record update, push, then mark P0-T06 verified
Approval needed: none
Secret/external-write status: no secrets handled; no external cloud calls

## 2026-08-31 - P2-T08 - exit

Executor: Codex root agent
Starting git state: clean and synchronized with `origin/main` at `5061ba7`
Scope: repair the stale handoff state and overbroad P2 exit gate
Actions: replaced present-tense dirty-work claims with current clean Git evidence and a clearly historical inventory; redefined P2 as generic protocol freeze; assigned concrete conformance to P3, P4-T07A, P5, and P6
Verification: `python3 -m unittest tests.test_adapter_contract tests.test_agent_adapter_contract -v` passed 9 tests; downstream ownership anchors were found; obsolete current-dirty headings were absent; `git diff --check` passed
Files changed: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: `a6b701d` plus this closeout record
Push: `a6b701d` pushed to `origin/main`; this closeout record is pushed in its follow-up commit
Decisions: P2 is verified only for the generic protocol; no concrete adapter is implemented or verified by this phase
Blocked items: none
Next exact action: commit and push, then claim P3-T01 and write the failing Herdr availability test
Approval needed: none
Secret/external-write status: no secrets handled; no cloud calls

## 2026-08-31 - P0-T06 - exit

Executor: Codex root agent
Starting git state: dirty worktree with prior DeepSeek/settings changes preserved
Scope: push governance documentation chain
Files intended: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Actions: marked P0 governance correction verified and set next task to P1-T01
Verification: documentation anchors and whitespace checks passed before commits; staged file checks excluded implementation work
Evidence: commits `3756677` and `7b516a1`, plus this final completion update, form the governance documentation chain
Files changed: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: this completion update is committed after editing
Push: pushed with governance documentation chain
Decisions: next default task is P1-T01; DeepSeek real closed loop remains P5 unless the user explicitly reprioritizes it
Assumptions: no cloud calls are authorized by this documentation-control task
Blocked items: none
Next exact action: begin P1-T01 or explicitly resume P5-T01/P5-T04
Approval needed: DeepSeek real-provider calls still need explicit per-run approval and test credential confirmation
Secret/external-write status: no secrets handled; no external cloud calls
