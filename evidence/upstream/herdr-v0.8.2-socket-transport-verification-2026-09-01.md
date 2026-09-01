# Herdr v0.8.2 Official Socket Transport Verification

Verified: 2026-09-01 Asia/Shanghai
Task: P3-T11 (master plan `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`)
Machine: macOS 26.6.2 (Build 25G83), Apple Silicon arm64

This is the P3-T11 runtime evidence: Forma AI's first real socket requests against the official verified Herdr v0.8.2 binary. The product now owns a thin official-transport binding (`forma_ai/herdr_transport.py`) behind the existing adapter seam; runtime state remains Herdr's. No product-owned runtime substitute, protocol reimplementation, or upstream fork was introduced. Event subscription, real agent integration, cancellation, and recovery remain P3-T12+ scope.

## Wire protocol (empirically validated against a live server)

Confirmed against live named test sessions, not only the bundled schema:

- Request envelope: `{"id": <string>, "method": <string>, "params": <object>}` — all three keys required; `ping` and `session.snapshot` take empty `params`.
- Success response: `{"id": ..., "result": {"type": <string>, ...}}` — the payload is discriminated on `result.type`.
- Error response: `{"id": ..., "error": {"code": <string>, "message": <string>}}` — **error responses may carry an empty `id`**, so correlation must not rely on id matching alone.
- Unsolicited event lines `{"event": ..., "data": ...}` carry no `id` and no `result`/`error` key.
- Consequence adopted by the transport: a response is located as the first line carrying a `result` or `error` key; other lines are skipped.

## Live results (verified binary, isolated named sessions)

`ping` → pong payload: version `0.8.2`, protocol `20`, capabilities `{"live_handoff": true, "detached_server_daemon": false}`.

`session.snapshot` on a fresh session → `session_snapshot` result with protocol `20`, empty `agents` and `panes` lists.

Adapter `availability()` with the transport probe wired reports `status: ready`, `reachable: true`, `ready: true`, `proof: ping_pong_verified` — binary presence is no longer mistaken for health (closes the availability half of the P1-T09 audit finding).

Test-session isolation: every live test creates a unique named session (`forma-p3t11-test-<uuid8>`), starts it with `herdr --session <name> server` (headless), and tears it down with `herdr session stop <name> --json` + `herdr session delete <name> --json`. The default session (`~/.config/herdr/herdr.sock`) is never started or contacted. Post-run residue check: `~/.config/herdr/sessions/` empty.

## Transport design points under test

- Fail-closed protocol gate: `ping` is verified before the first real request (once per transport instance); a protocol other than 20, a non-pong payload, or a rejected ping raises `HerdrProtocolError` and blocks every call.
- Socket path resolution order: explicit path → `HERDR_SOCKET_PATH` → `HERDR_SESSION` (named: `~/.config/herdr/sessions/<name>/herdr.sock`) → default (`~/.config/herdr/herdr.sock`); empty env values fall through.
- One connection per request; connection failures and malformed lines raise `HerdrTransportError`; server error responses raise `HerdrRequestError(code, message)` even when the response id is empty.
- Adapter behavior is unchanged when no probe is configured (binary-presence reporting preserved); probe health maps `HerdrProtocolError` → `incompatible` / `HERDR_PROTOCOL_INCOMPATIBLE`, transport/OS errors → `unreachable` / `HERDR_SOCKET_UNREACHABLE`, validated pong → `ready`.

## Test coverage at closeout

New: 24 tests — 18 in `tests/test_herdr_transport.py` (11 transport unit tests with a scripted fake socket factory, 5 socket-path resolution tests, 2 live tests against the verified binary; live tests skip cleanly when the binary is absent) and 6 probe/availability tests in `tests/test_herdr_adapter.py`. Red-green flow: the new tests failed before the transport module and probe seam existed (`ModuleNotFoundError` / missing keyword), then passed after implementation.

Full suite: `python3 -m unittest discover tests` → 271 tests, OK, 1 skipped (expected real-Semantica integration test).

## Runtime/schema discrepancy observed (ledger note)

While validating the wire protocol, an error response listing the server's accepted methods included `pane.graphics.stream`, which is absent from the bundled schema's 91-method request `oneOf`. The live server therefore accepts at least one method the bundled schema does not document. Recorded in the capability ledger's discrepancy notes alongside the `pane.run` finding from P3-T10; P3-T12 must continue to use only schema-documented methods.

## Verification commands (reproducible)

```
python3 -m unittest tests.test_herdr_transport tests.test_herdr_adapter -v
python3 -m unittest discover tests
ls ~/.config/herdr/sessions/   # live-test residue check: empty
git diff --check               # clean
```

Live tests locate the binary via `FORMA_HERDR_TEST_BINARY` or the canonical product download path `~/Library/Application Support/Forma AI/cache/downloads/herdr-macos-aarch64` (the P3-T10 verified artifact).
