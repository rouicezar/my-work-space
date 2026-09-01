# Herdr v0.8.2 Two Real Fixture-Agent Isolation Verification

Verified: 2026-09-01 Asia/Shanghai
Task: P3-T12 (master plan `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`)
Machine: macOS 26.6.2 (Build 25G83), Apple Silicon arm64

This is the P3-T12 runtime evidence: two real fixture agents ran in parallel through the official Herdr v0.8.2 binary in one isolated named session, on two distinct panes with distinct working directories, with verified parallel execution, working graceful cancel, and no input, state, artifact, or cross-pane output leakage. The product owns only three thin adapter methods over schema-documented Herdr methods; runtime state remains Herdr's. No product-owned runtime substitute or undocumented method was introduced.

## Upstream search result and integration decision (upstream-first rule)

Before implementing, the fixture flow was probed against the verified binary in disposable sessions (`forma-p3t12-probe-*`, `forma-p3t12-types-*`):

- A fresh headless named session starts with 0 workspaces and 0 panes; `workspace.create` must come first. Its success result `workspace_created` carries `workspace`, `tab`, and `root_pane` — the root pane is the first fixture pane.
- `pane.split` (schema requires only `direction`; optional `target_pane_id`, `cwd`) creates the second pane and returns `pane_info`. **Correction to the P3-T10-era ledger wording**: `pane.split` has no command field — commands enter panes only via `pane.send_text`.
- `pane.report_agent` (required `pane_id`, free-string `source`, `agent`, enum `state` idle/working/blocked/unknown) is the schema-documented client-reporting hook. Reported agents appear in `agent.get`, `agent.list`, and `session.snapshot` with real `agent_status` transitions — this is the mechanism that makes fixture agents real Herdr agents, not a product-side simulation.
- Confirmed live response types: `workspace.create` → `workspace_created`, `pane.split` → `pane_info`, `pane.send_text` → `ok`, `pane.wait_for_output` → `output_matched`, `pane.report_agent` → `ok`, `pane.read` → `pane_read`.
- Echo pitfall (observed live): `pane.wait_for_output` also matches the echoed input line, and pane text contains the echoed command verbatim. All completion markers therefore use `echo "MARKER-$(date +%s)"` and are matched as `MARKER-[0-9]+` — only executed output contains the expanded timestamp.
- Probe runs also demonstrated parallel execution, cancel, and isolation before any product code was written.

Integration decision: three thin methods on `HerdrAdapter` — `open_workspace` (`workspace.create`), `open_pane` (`pane.split`), `spawn_reported_task` (`pane.send_text` → `pane.report_agent` → `agent.get`). Fixture tasks reuse the existing `task_status` / `cancel_task` lifecycle unchanged. License obligation: Apache-2.0, external process, official artifact only — unchanged from P3-T10/T11.

## Live isolation proof (`tests/test_herdr_integration.py`)

Single live test `test_two_fixture_agents_run_in_parallel_without_leakage` against the verified binary in a unique named session (`forma-p3t12-test-<uuid8>`, headless `server`, torn down with `session stop` + `session delete`; default session never contacted):

1. **Two distinct panes, two distinct cwds**: `open_workspace(cwd=<dir_a>, label="forma-p3t12")` → root pane; `open_pane(direction="right", target_pane_id=<root>, cwd=<dir_b>)` → second pane. Distinct pane ids, same workspace, distinct temp working directories.
2. **Parallel execution proven**: agent A's command writes `a_start.txt` then `sleep 8`; agent B's writes `b_start.txt`, `sleep 2.5`, `b_end.txt`. Measured `b_end - a_start < 8` — B finished inside A's sleep window, which is impossible under serialized execution.
3. **Real Herdr state, not product state**: both agents were reported via `pane.report_agent` and observed through `agent.get` with `agent_status: working` while running; the final `session.snapshot` listed exactly `fixture-agent-a` and `fixture-agent-b`, both `idle`, on distinct pane ids.
4. **Graceful cancel works and is pane-exact**: `cancel_task` on A (revision-checked) sent `ctrl+c` to A's pane only; the `^C` interrupted the sleep, B completed untouched.
5. **No artifact leakage**: A's command chain after the sleep (`echo A-LEAK > a_leak.txt; echo "A-FINISHED-$(date +%s)"`) never executed — `a_leak.txt` absent, `dir_a` contains only `a_start.txt`, and executed-output marker `A-FINISHED-[0-9]+` never appears in pane A's text. `dir_b` contains exactly `b_start.txt`, `b_end.txt`.
6. **No input or cross-pane output leakage**: pane A's text contains no `B-DONE` substring (neither echoed nor executed); pane B's text contains no `A-READY` and no `A-LEAK`. Executed-output markers `A-BACK-[0-9]+` / `B-DONE-[0-9]+` appear only in their own panes.

## Adapter design points under test (unit level)

`tests/test_herdr_adapter.py` `HerdrAdapterFixtureTests` (5 tests) pin the exact wire behavior with an injected request boundary:

- `open_workspace` sends `workspace.create` with only the non-None optional params (`{}` when none given), validates `workspace_created`, and extracts `workspace_id` + `root_pane_id`.
- `open_pane` sends `pane.split` with `direction` plus only the non-None optionals, validates `pane_info`, and extracts `pane_id` + `workspace_id`.
- `spawn_reported_task` drives the exact sequence `pane.send_text` (`{pane_id, text}`) → `pane.report_agent` (`{pane_id, source: "forma-fixture", agent, state: "working"}`) → `agent.get` (`{target: pane_id}`), validates each response type, and returns a `HerdrTask` with run_id `herdr:<task_id>:<pane_id>` registered in all three run-id registries — so fixture tasks cancel through the existing `cancel_task` path unchanged (verified by test).
- `correlation_id` stays product-side metadata only (accepted, not sent) — consistent with the "product saves correlation metadata, Herdr owns runtime state" boundary.

## Test coverage at closeout

Red-green flow: the 6 new tests (5 adapter unit + 1 live integration) first failed for the correct reason (`AttributeError: 'HerdrAdapter' object has no attribute 'open_workspace'/'open_pane'/'spawn_reported_task'`), then passed after implementing the three methods. One intermediate live-test failure was an over-strict assertion matching the echoed input line (not a product bug); it was corrected to timestamp-regex matching of executed output only.

Full suite: `python3 -m unittest discover tests` → **277 tests, OK, 1 skipped** (expected real-Semantica integration test).

## Residue and hygiene checks

- Post-run: `~/.config/herdr/sessions/` empty; default session socket `~/.config/herdr/herdr.sock` absent.
- `git diff --check` clean.
- Live test skips cleanly when the verified binary is absent (locates it via `FORMA_HERDR_TEST_BINARY` or the canonical product download path `~/Library/Application Support/Forma AI/cache/downloads/herdr-macos-aarch64`).

## Verification commands (reproducible)

```
python3 -m unittest tests.test_herdr_adapter -v          # 16 tests OK (5 new)
python3 -m unittest tests.test_herdr_integration -v      # 1 live test OK
python3 -m unittest discover tests                       # 277 OK, 1 skipped
ls ~/.config/herdr/sessions/                             # empty
git diff --check                                         # clean
```

## Scope boundaries (what this does NOT yet close)

- Event subscription (`session.subscribe` / event stream) and workbench presentation binding remain P3-T13.
- Real wait/blocked/artifact-read surfaces beyond the fixture markers, and cancel of Herdr-native agents (vs. reported fixture agents), remain P3-T14.
- Detach/reconnect and native resume in a live session remain P3-T15.
- `agent.start` (Herdr-native agent launch) is not used here; fixture agents use the schema-documented `pane.report_agent` hook, which is the upstream-documented way for a client to report agent activity.
