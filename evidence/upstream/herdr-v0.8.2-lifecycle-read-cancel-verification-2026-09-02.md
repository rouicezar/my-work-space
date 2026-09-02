# Herdr v0.8.2 Lifecycle, Read, and Cancel Verification

Verified: 2026-09-02

## Scope

P3-T14 binds only the official pinned Herdr v0.8.2 socket surfaces for task wait, bounded output read, process reconciliation, graceful interrupt, and explicit force-close escalation. Herdr remains the lifecycle and terminal-output authority. Forma AI retains only correlation, bounded-read, and cancellation-policy state.

## Upstream contract

The verified binary's bundled protocol-20 schema declares:

- `agent.wait` with required `target` and optional `until` and `timeout_ms`.
- `agent.read` with required `target` and `source`, optional `lines`/`format`, and `strip_ansi` defaulting to true.
- `pane.read` with equivalent pane-targeted read controls.
- `pane.process_info` with optional `pane_id`.
- `pane.send_keys` with required `pane_id` and key array.
- `pane.close` with required `pane_id`.

The read-source enum is `visible`, `recent`, `recent_unwrapped`, or `detection`; the read-format enum is `text` or `ansi`.

## Disposable-session probes

All probes used a fresh `forma-p3t14-*` named session, an isolated temporary HOME/PATH, and a provider-free repository-local Codex fixture. No production or default Herdr session, cloud/model provider, credential, network request, or user shell configuration was used.

Observed wire behavior:

- `agent.wait(target, until=["idle"], timeout_ms=1000)` returns `agent_info`; unmatched `blocked` returns the server error `timeout: timed out waiting for agent status`.
- `agent.read(..., format="text", strip_ansi=true)` returns `pane_read`, not an agent-specific envelope. A very small `recent` line window can be empty with `truncated: true`; a bounded 50-line request returned the complete blocked fixture transcript without ANSI control codes.
- `pane.process_info` returns `pane_process_info` with the authoritative pane id, shell pid, and foreground process records.
- `pane.close` returns `ok`; a subsequent `agent.get` for the target pane returns `agent_not_found`.
- Herdr's real Codex detector marks the provider-free fixture `blocked` when its terminal title is `Action Required`. `agent.prompt(... wait until blocked)` returned `agent_prompted` with `agent_status: blocked`; `agent.wait(... until=["blocked"])` returned `agent_info` with the same blocked status; `agent.explain` reported `osc_title_blocked`.

## Adapter policy

`HerdrAdapter` now maps these direct upstream surfaces without recreating an execution state machine:

- `wait_for_task` maps `agent.wait`, preserves the authoritative task revision, and rejects pane or terminal-identity replacement.
- `read_task_output` always requests text with `strip_ansi: true` and accepts only 1 through 200 lines.
- `task_process_info` maps `pane.process_info` to the pane id, shell pid, and foreground process ids.
- Graceful `cancel_task` re-reads `agent.get` and `pane.process_info`, rejects revision/terminal drift or no foreground process, then sends `ctrl+c` to the exact pane.
- `force_cancel_task` requires a matching prior graceful claim plus `force_confirmed=true`, rechecks the same revision, terminal id, and foreground process ids, calls `pane.close` only after those checks, and proves closure through `agent_not_found`.
- Independent review found that `task_status` could previously overwrite a claimed run with a replacement terminal returned for the same pane. The corrected refresh path now rejects workspace, pane, or terminal replacement before updating cached state, so a status refresh cannot redirect later cancellation to another Agent.
- Foreground process ids are normalized before comparison, and confirmed force close removes every run-to-task, run-to-pane, task-cache, and cancellation-claim entry.

## Verification

- New and corrected P3-T14 adapter policy tests: 5 passed, including replacement-terminal rejection and complete post-close registry invalidation.
- Live P3-T14 blocked/read/cancel test against the pinned binary: passed.
- Focused Herdr transport/adapter/presentation/integration suite: 55 passed.
- Live Herdr integration tests: 3 passed.
- Full Python suite: 298 passed, 1 expected skip.
- Swift package suite: 43 passed, 2 environment-gated Keychain skips.
- `git diff --check`: passed.
- Disposable-session residue check: no `forma-p3t14-*` session directories remained.
- One stopped historical `forma-p3t13-test-0ce468a1` directory from an earlier run was discovered during the broader residue check and deleted through Herdr's exact `session delete` command; it contained only session metadata and a server log.

## Boundary

This evidence does not prove provider-native resume, detach/reconnect across an application restart, runtime UI replacement of Preview cards, local Qwen inference, or cloud execution. Those remain P3-T15/P3-T16 and P5 work.
