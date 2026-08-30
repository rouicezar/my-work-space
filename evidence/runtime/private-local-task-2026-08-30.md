# Private local task evidence — 2026-08-30

## Contract

The daily local-task protocol accepts a versioned prompt body only through Supervisor
standard input. It limits the request to 1 MiB, prompt UTF-8 to 256 KiB, and output to
4,096 tokens. The prompt is not a command argument or environment variable. Runtime
credentials remain Keychain-backed child-environment values.

The first contract is text-only and non-streaming. It rejects empty or malformed
input, oversized prompts, inconsistent token usage, a different returned model, empty
content, and model tool calls. A stopped or unhealthy local runtime fails without
creating a cloud proposal.

## Automated evidence

- Full Python suite after unified routing integration: `223` passed, `1` skipped.
- Swift package after native protocol integration: `29` passed, `2` environment-gated
  tests skipped in the ordinary run.
- Standard-input and secret-environment fixtures prove that prompt and runtime secrets
  do not enter arguments.
- Process identity now binds the observed command digest and process start time. This
  avoids false degradation when macOS reports a resolved Python runtime path while
  retaining exact identity checking.

## Real reused-Qwen run

The environment-gated native-client integration was then enabled against:

- Product root: an isolated per-user Application Support directory
- Managed runtime: oMLX v0.6.3
- Model: the previously verified zero-copy Qwen reference

The test started oMLX, the authenticated broker, and the memory service; confirmed all
three were alive; ran the existing fixed health sample; then submitted an arbitrary
Chinese prompt through `local-task`. It received a non-empty result with `route=local`.
The correlation ID appeared in `logs/audit/inference.jsonl`, while the prompt, result,
and all three runtime secrets did not.

The test stopped the runtime. Final authoritative state was `phase=stopped`, all three
process records were null, and a process-table check found no remaining product oMLX,
broker, or memory process.

## Unified task routing evidence

The versioned `task-submit` protocol now derives runtime health and measured available
memory inside Supervisor, binds the discovered runtime model to the verified local
profile, and returns exactly one of `local`, `cloud_proposal_required`, or
`capability_unavailable`. Tests cover local execution, cloud disabled, offline proposal
creation, blocked data, stale cloud pricing, and local-result validation failure. The
cloud-proposal branches assert that no DeepSeek network execution occurs.

A release-mode app bundle was built with the frozen Supervisor, routing catalogs, and
this evidence file. The bundle's ad-hoc signature passed strict deep verification, and
the frozen Supervisor exposed `task-submit`. This is packaging evidence only, not
Developer ID signing, notarization, clean-machine installation, or release proof.

## Failure found and corrected during the run

The first real run exposed a false-degraded state: broker and memory were alive, but
their saved launcher path differed from the resolved Python executable shown by macOS.
The test stopped oMLX but could not recognize the two child processes; they were
identified exactly and stopped. Identity matching was then changed to observed command
digest plus process start time, covered by a regression test, and the complete real run
passed on retry with clean shutdown.

## Remaining boundary

This proves the real native-client-to-Supervisor-to-broker-to-Qwen task path and the
synthetic three-route orchestration contract, but it is not yet ordinary-user
acceptance. A real approved DeepSeek request, the daily workbench UI, visible
progress/cancel behavior, and the novice-user test remain open.
