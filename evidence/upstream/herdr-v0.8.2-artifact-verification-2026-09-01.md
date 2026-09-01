# Herdr v0.8.2 Official Artifact Verification

Verified: 2026-09-01 Asia/Shanghai
Task: P3-T10 (master plan `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`)
Machine: macOS 26.6.2 (Build 25G83), Apple Silicon arm64

This is the P3-T10 installer/runtime evidence: the official pinned Herdr release artifact was acquired through the product's own digest-gated downloader and verified on the five required dimensions — digest, version, protocol, schema, and license. No product-owned runtime substitute was introduced. The socket transport binding remains P3-T11 scope.

## Acquisition

- Manifest entry: `config/upstreams.json` component `herdr`, artifact `macos-aarch64` (added this task, with the sibling `macos-x86_64` pin).
- Downloader: `forma_ai.downloads.ResumableDownloader` (product-owned, resumable, digest-gated; no ad-hoc curl).
- Download directory: `~/Library/Application Support/Forma AI/cache/downloads/` (canonical product root, oMLX layout precedent).
- Network behavior: attempts 1–2 failed with `TRANSFER_INTERRUPTED` (read timeout, github.com intermittency); attempt 3 resumed from the 2 MiB partial and completed. The resume path of the crash-safe downloader was exercised for real, not simulated.
- Final file: `herdr-macos-aarch64`, Mach-O 64-bit executable arm64.

## Check 1 — Digest and size

`scripts/verify_artifact.py herdr <path> --platform macos --os-major 26 --architecture aarch64` (exit 0):

- expected/actual size: 18,969,952 bytes — match
- expected/actual SHA-256: `a5d4f4d504d8b309c91f811050559300faba31258425f53c50852fc96f6ae574` — match
- Independent re-hash with `/usr/bin/shasum -a 256`: same digest.

The same gate also ran inside `ResumableDownloader.fetch` before the `.part` file was promoted.

## Check 2 — Version

`herdr --version` on the verified binary (after `chmod +x`) reports `herdr 0.8.2`, matching the pinned release `v0.8.2`.

## Check 3 — Protocol

`herdr api schema --json` reports `"protocol": 20`, `"schema_version": 1`. Protocol version is taken from the official binary itself, as required; the adapter must check it at startup and fail closed on incompatibility (binding is P3-T11).

## Check 4 — Bundled schema

The schema document parses as valid JSON Schema (draft 2020-12) and covers the five documented top-level domains: `request`, `success_response`, `error_response`, `event`, `subscription_event`.

- 91 request methods, including every runtime method the capability ledger's control map depends on: `ping`, `session.snapshot`, `events.subscribe`, `events.wait`, `workspace.create/list/get/close/focus/move/rename`, `tab.create/*`, `pane.split/close/read/send_text/send_input/send_keys/process_info/report_agent/report_agent_session/wait_for_output`, `agent.start/list/get/prompt/read/wait/explain/send_keys/rename`, `worktree.list/create/open/remove`, `integration.install/uninstall`, `server.stop`, `layout.*`.
- 26 event kinds covering workspace/tab/pane lifecycle, focus, layout updates, `pane_agent_detected`, `pane_agent_status_changed`, `pane_output_changed`, `pane_exited`, and worktree lifecycle events.
- 3 subscription kinds: `pane.agent_status_changed`, `pane.output_matched`, `pane.scroll_changed`.

CLI surface confirmed via `herdr --help`: socket-API helper subcommands for `api`, `workspace`, `worktree`, `tab`, `agent`, `pane`, `session`, `integration`, `notification`; plus `status`, `update [--handoff]`, `channel`, `server stop/reload-config`.

### Observation for P3-T12 planning (no plan change)

The ledger's control map listed `pane.run`, but the official schema has no `pane.run` method. The schema's actual path for running things in panes is `pane.split` (creates a pane with a command) plus `pane.send_text`/`pane.send_input` and `agent.start`. P3-T12 (two real fixture agents) must use the schema-documented methods; the ledger table row will be corrected when the transport lands.

## Check 5 — License

Herdr v0.8.2 is Apache License 2.0 per the immutable pinned release metadata already recorded in `docs/research/herdr-capability-ledger.md` (Cargo.toml and LICENSE at tag `v0.8.2`, commit `9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c`). No upstream source, names, or trademarks were copied into the product; the acquired bytes are the official release asset only. Attribution and license material obligations for distribution remain tracked in the ledger and the P8 release chain.

## Distribution-relevant observation (P8 gate)

The binary carries only `com.apple.provenance` (no `com.apple.quarantine`, because acquisition used the product downloader, not a browser download). It executed from Terminal without Gatekeeper escalation. Developer ID signing/notarization of anything that bundles or installs this binary remains a P8 gate item and is unchanged by this task.

## Verification commands (reproducible)

```
python3 scripts/verify_artifact.py herdr \
  "$HOME/Library/Application Support/Forma AI/cache/downloads/herdr-macos-aarch64" \
  --platform macos --os-major 26 --architecture aarch64
herdr --version                      # the verified binary, after chmod +x
herdr api schema --json | python3 -c 'import json,sys; s=json.load(sys.stdin); print(s["protocol"], s["schema_version"])'
python3 -m unittest discover tests -v
```

Test suite at closeout: 247 tests, OK, 1 skipped (expected), including five new red/green tests for architecture-discriminated artifact selection.
