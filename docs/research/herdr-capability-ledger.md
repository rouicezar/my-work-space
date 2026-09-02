# Herdr Capability and Integration Ledger

Verified: 2026-09-03 Asia/Shanghai

This is a pinned upstream capability map, not release acceptance. The official artifact and socket transport are verified (P3-T10/T11); two provider-free fixture agents run through official `agent.start` with parallel/cancel/isolation proof (corrected P3-T12); snapshot-first presentation binding has real live-event plus forced server-side socket-loss evidence (P3-T13); official wait, real blocked truth, bounded ANSI-stripped read, process reconciliation, graceful interrupt, and explicit force-close policy are verified (P3-T14); detach/reconnect with stale-reference fail-closed and explicit fresh-run are verified (P3-T15); real runtime agent cards and digest-verified Herdr lifecycle management are verified (P3-T16); and the P3 phase is closed with the full real integration suite plus manual task review (P3-T17, 2026-09-03). Provider-native session resume remains gated on a separately approved real-provider probe. Every capability below is sourced from the official v0.8.2 release, pinned source, bundled schema, versioned documentation, or the recorded live probes.

## Immutable evidence snapshot

- Canonical repository: `herdrdev/herdr`
- Release/tag: `v0.8.2`
- Annotated tag object: `34ba52cc6ff3b723e6fc0130485ec24582dbe205`
- Tag target commit: `9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c`
- Tag verification: unsigned
- GitHub release metadata: stable and `immutable: true`
- Package: Rust 2021 binary, version `0.8.2`, Apache-2.0
- macOS Apple Silicon artifact: `herdr-macos-aarch64`, 18,969,952 bytes, SHA-256 `a5d4f4d504d8b309c91f811050559300faba31258425f53c50852fc96f6ae574`
- macOS Intel artifact: `herdr-macos-x86_64`, 20,551,504 bytes, SHA-256 `ab50262c8190cd7aa9056d249d255c08c328c3e8716de9cfa29db4f131b8e2c1`

The unsigned tag is not trusted by name alone. Acquisition must bind the target commit or the immutable release asset and its published digest, then verify the downloaded bytes before execution.

## License boundary

Herdr v0.8.2 uses the standard Apache License 2.0. Source and binary reuse are permitted subject to the license, including providing the license, marking modified files, retaining applicable notices, and respecting the trademark exclusion. Forma AI must include Herdr attribution and license material in any distribution that contains the binary or derived source. Product naming and visuals must remain Forma AI's own.

## Runtime role decision

Herdr is the mandatory core multi-agent execution runtime. It owns agent terminal processes, workspaces/tabs/panes, semantic agent state, event-driven waits, detach/reattach, session shape, and supported native agent resume. Forma AI owns the native workbench, user intent, policy/approval, task graph, provider routing, Semantica memory governance, audit correlation, and adapter lifecycle.

The preferred first integration is the official pinned binary through CLI wrappers for simple commands and the local socket API for snapshots, subscriptions, and precise request/response control. Reimplementing the Herdr runtime or replacing it with cosmetic parallel UI is prohibited unless a verified platform, security, license, or compatibility blocker is recorded.

## Granular control-surface map

| Forma AI requirement | Pinned Herdr surface | Reuse decision | Required acceptance evidence |
|---|---|---|---|
| Runtime identity and compatibility | `ping`, `herdr status`, protocol version; bundled schema via `herdr api schema --json` | Direct reuse | Verify binary digest, version, protocol version, schema parse, and unknown-field tolerance before enabling dispatch. |
| Initial state bootstrap | `session.snapshot` / `herdr api snapshot` | Direct reuse | Snapshot returns version/protocol metadata, focused IDs, workspaces, tabs, panes, layouts, and agents; Forma cache rebuild test passes. |
| Long-lived state updates | `events.subscribe`, `events.wait`; workspace/tab/pane/layout/worktree lifecycle events | Direct reuse | Reconnect/resubscribe test proves no stale UI after socket loss; refresh with `session.snapshot` after reconnect. |
| Parallel agent placement | `workspace.create`, `tab.create`, `pane.split`, `pane.run`, `agent.start` | Direct reuse | Start at least two fixture agents in distinct panes with stable public IDs and observable concurrent states. |
| Agent discovery and state | `agent.list`, `agent.get`, `agent.explain`; `pane.report_agent`; official integration assets under `src/integration/assets/*` | Direct reuse | Codex and Claude fixtures report authoritative `idle`, `working`, `blocked`, `done`, or `unknown`; display metadata cannot override lifecycle state. |
| Agent prompting | `agent.prompt` with optional atomic `wait`; blocked agents return `agent_blocked` | Direct reuse | Prompt reaches the correct pane; no race between send and wait; blocked approval/question state fails closed without injected input. |
| Readable output and diagnostics | `agent.read`, `pane.read`, `pane.process_info`, `agent.explain` | Direct reuse | Bounded ANSI-stripped output reaches the adapter; process and detector evidence are correlated without persisting output by default. |
| Wait and synchronization | `agent.wait` is server-owned, event-driven, and pins the resolved pane occupant; `pane.wait_for_output` | Direct reuse | Real blocked and timeout outcomes are observed; a terminal-identity change is rejected by the adapter before the result is accepted. |
| Interrupt/cancel | Pane input/keys plus `pane.close`; process control remains terminal-owned | Adapter policy required | Graceful interrupt rechecks the claimed revision, terminal, and foreground process; forced termination needs a matching graceful claim, a second confirmation, fresh reconciliation, and `agent_not_found` after closure. |
| Resume after agent restart | Official native session references via `pane.report_agent_session`; Codex integration v5+ uses `codex resume`, Claude Code v6+ uses `claude --resume` | Unverified; not yet reused | The provider-free repository fixture never reports an `agent_session`, so native resume cannot be truthfully proven from it. `HerdrAdapter` has no `resume_task()` method; a prior mock-only implementation that fabricated this capability was removed 2026-09-02 (P3-T15). Native resume remains blocked on a separately approved real-provider probe. |
| Detach/reconnect | Background server plus client detach/reattach | Direct reuse | Closing the workbench does not terminate approved running tasks; reopening reconstructs state from snapshot/events. |
| Server restart recovery | Saved session shape; optional pane history; native agent resume | Direct reuse with privacy defaults | Verify layout/cwd/focus restoration separately from process survival. Keep pane history disabled by default because it may contain secrets and prompts. |
| Update continuity | Experimental `--handoff` transfers live panes best-effort; in-flight requests, waits, subscriptions, sockets, and messages may be interrupted | Gated reuse | Keep disabled until update/rollback tests prove reconnect and retry behavior. Never report handoff success solely from server health. |
| Worktree isolation | `worktree.list`, `worktree.create`, `worktree.open`, `worktree.remove` | Reuse candidate | Verify repository boundaries, branch rules, dirty-tree behavior, and that remove never silently deletes a branch. |
| Layout and ownership visibility | Workspace/tab/pane IDs, labels, focus, layouts, process info, agent state | Direct reuse, product-owned presentation | Forma AI renders its own macOS UI but uses authoritative Herdr IDs/state; no duplicate state machine may compete with the runtime. |
| External integrations/plugins | `integration.install/uninstall`; plugin link/list/enable/action/log/pane APIs | Disabled by default | Each integration/plugin requires explicit origin, permission, executable, data-egress, and uninstall review. |
| Remote operation | `herdr --remote` and remote attach flows | Exclude from initial local-first release | Later task must define host trust, transport/authentication, consent, availability, and audit before exposure. |

## Transport and security facts

- The raw protocol is newline-delimited JSON over a Unix-domain socket on macOS/Linux and a named pipe on Windows.
- Named sessions have separate sockets; resolution considers explicit session, `HERDR_SOCKET_PATH`, `HERDR_SESSION`, then the default path.
- Managed pane processes receive Herdr-owned environment variables including socket, workspace, tab, and pane identity. Forma AI must not place credentials or raw secrets in process arguments, labels, metadata, or audit logs.
- The schema covers requests, success responses, error responses, emitted events, and subscription events and is bundled with the installed binary.
- Protocol compatibility is versioned. The adapter must check it at startup and fail closed on incompatible protocol, not guess from the executable version.
- Pane screen history is off by default because terminal output may include credentials, prompts, tokens, and command output. Forma AI keeps it off unless a later privacy setting provides informed opt-in and retention/deletion controls.

## State and recovery semantics

Herdr distinguishes four materially different cases:

1. Detach/reattach keeps the original processes and live terminal state.
2. Server restart restores layout/cwd/focus, not arbitrary running processes.
3. Optional pane-history replay restores screen text, not the old process.
4. Official native agent session restore can restart supported agents from their reported session references.

Experimental live handoff may preserve pane processes during server replacement, but it does not preserve in-flight API calls, waits, subscriptions, sockets, or pane messages. Forma AI recovery logic must reconnect, obtain a fresh snapshot, resubscribe, and reconcile task ownership before declaring recovery.

## Source entry points

The pinned tree exposes reusable protocol and runtime code at:

- `src/api/client.rs`, `src/api/server.rs`, `src/api/schema/*`, `src/api/subscriptions.rs`, and `src/api/wait.rs`
- `src/cli/agent.rs`, `src/cli/api.rs`, `src/cli/pane.rs`, and `src/cli/server.rs`
- `src/app/api/agents.rs`, `src/app/api/panes.rs`, `src/app/api/session.rs`, `src/app/api/worktrees/*`
- `src/server/*`, including socket paths, client transport, handoff, headless operation, and notifications
- `src/pane/agent_detection.rs`, `src/agent_resume.rs`, and official agent integration assets under `src/integration/assets/*`
- `docs/next/api/herdr-api.schema.json` and the pinned socket/session documentation

These paths are upstream entry points, not permission to fork them immediately. The binary/socket integration should be attempted first because it preserves upstream ownership and upgrade separation.

## Open validation gaps

- CLOSED 2026-09-01 (P3-T10): the official `herdr-macos-aarch64` release asset was downloaded through the product's `ResumableDownloader` (resume path exercised against real network interruptions) and digest/size-verified against the pinned expectation; version `0.8.2`, protocol `20`, and the bundled schema were verified from the official binary itself. Evidence: `evidence/upstream/herdr-v0.8.2-artifact-verification-2026-09-01.md`.
- CLOSED 2026-09-01 (P3-T11): the official socket transport binding has run real requests in Forma AI against the verified binary — live `ping` (pong: version 0.8.2, protocol 20) and `session.snapshot` in isolated named test sessions, plus a fail-closed protocol gate, envelope/error/event line handling, and socket-path resolution, all under unit and live tests. Runtime state stays with Herdr; the product owns only the thin binding. Evidence: `evidence/upstream/herdr-v0.8.2-socket-transport-verification-2026-09-01.md`.
- CLOSED WITH CORRECTION 2026-09-02 (P3-T12): the 2026-09-01 `pane.report_agent` shell proof was insufficient and its real-agent acceptance was withdrawn. The corrected test launches two provider-free repository fixtures through official `agent.start`, rejects `launch_pending`, waits for Herdr-detected idle state, refreshes through `agent.get`, and requires distinct run/pane/terminal/name identities plus `agent=codex` and `interactive_ready=true`. Concurrent work, pane-exact graceful cancel, artifact isolation, and output isolation pass in an isolated named session with deterministic PATH/HOME and automatic temporary cleanup. Evidence: `evidence/upstream/herdr-v0.8.2-two-fixture-agent-isolation-verification-2026-09-01.md` correction section.
- CLOSED 2026-09-02 (P3-T13): a real server-side socket loss now changes the presentation to `stale` and all old agents to `unknown` before recovery. A fresh `session.snapshot` reconciles authoritative identities/revisions before resubscription; old panes disappear after server restart and a new pane receives resumed live transitions. Live v0.8.2 status events omit revision/sequence, so they are treated as invalidation hints followed by an authoritative snapshot read rather than assigned a fabricated product revision. The Supervisor envelope and Swift `RuntimePresentationProvider` preserve this fail-closed mapping. Evidence: `evidence/upstream/herdr-v0.8.2-presentation-reconnect-verification-2026-09-02.md`.
- CLOSED 2026-09-02 (P3-T14): a provider-free agent started through official `agent.start` reaches real `blocked` truth by Herdr's Codex detector (`osc_title_blocked`); `agent.prompt` and `agent.wait` both return that status. The adapter maps `agent.wait`, bounded 1–200-line ANSI-stripped `agent.read`, and `pane.process_info`. Graceful interrupt rechecks claimed revision, terminal identity, and foreground process; force close requires the completed graceful claim, a second explicit confirmation, fresh identical reconciliation, official `pane.close`, and a succeeding `agent_not_found` check. Evidence: `evidence/upstream/herdr-v0.8.2-lifecycle-read-cancel-verification-2026-09-02.md`.
- CLOSED WITH SCOPE CORRECTION 2026-09-02 (P3-T15): a discarded adapter client's task is reclaimed by a fresh `HerdrAdapter` only after a `session.snapshot()` and a subsequent `agent.get` both exactly match the caller-held claim's workspace, pane, terminal, revision, and normalized state; any mismatch (proven live with a stale-revision case) fails closed with no rebinding. The caller can then explicitly choose `start_fresh_task()`, which keeps the product `task_id` but requires and verifies a new pane/terminal/run identity in a live isolated session. Native provider-session resume is explicitly NOT proven by this task: the fixture never emits `agent_session`, and the previously existing `resume_task()` (an unverified mock-only fabrication that issued an unproven second `agent.start`) was removed rather than kept as a false capability claim. Evidence: `evidence/upstream/herdr-v0.8.2-detach-fresh-run-recovery-verification-2026-09-02.md`.
- REMAINING: provider-native session resume (requires a separately approved real-provider probe), confirmation/audit integration above the adapter boundary, and persistent recovery/task-history storage (P7-T02) remain open. Preview-card replacement and runtime data (P3-T16) and the P3 phase closeout (P3-T17) are complete.
- Cancellation has no single high-level `agent.cancel` method in the reviewed control map; the P3-T14 policy maps available pane/process controls but does not replace Herdr lifecycle authority.
- Resume support depends on the installed official integration version and the external agent's native session behavior.
- Live handoff remains experimental and is not initial acceptance evidence.
- Remote operation, updater ownership, plugin execution, and pane-history retention remain separately gated.
- Schema discrepancy noted 2026-09-01 (P3-T10, wording corrected 2026-09-01 by P3-T12 live probing): the control map above lists `pane.run`, but the official v0.8.2 schema has no such method. The documented path is `pane.split` (creates an empty pane — live probing confirms it has no command field) plus `pane.send_text`/`pane.send_input` for commands and `agent.start` for native agents; `workspace.create` returns the root pane. Forma AI uses only schema-documented methods.
- Schema discrepancy noted 2026-09-01 (P3-T11): the live v0.8.2 server accepts `pane.graphics.stream` (seen in a server error message listing accepted methods), but the bundled schema's 91-method request `oneOf` does not document it. The runtime method surface is therefore at least one method larger than the bundled schema; Forma AI must keep using only schema-documented methods and re-check the surface on every pinned-version bump.

## Primary sources

- [Herdr v0.8.2 release](https://github.com/herdrdev/herdr/releases/tag/v0.8.2)
- [Pinned source tree](https://github.com/herdrdev/herdr/tree/9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c)
- [Package manifest](https://github.com/herdrdev/herdr/blob/9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c/Cargo.toml)
- [Apache-2.0 license](https://github.com/herdrdev/herdr/blob/9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c/LICENSE)
- [Socket API documentation](https://github.com/herdrdev/herdr/blob/9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c/docs/next/website/src/content/docs/socket-api.mdx)
- [Session state and restore](https://github.com/herdrdev/herdr/blob/9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c/docs/next/website/src/content/docs/session-state.mdx)
- [Bundled API schema](https://github.com/herdrdev/herdr/blob/9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c/docs/next/api/herdr-api.schema.json)
