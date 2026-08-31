# Forma AI Agent Adapter Contract v1

Status: accepted protocol specification for adapter implementations. This document defines behavior; it does not claim that Codex, Claude, or another agent is already integrated.

## Authority and transport

Forma AI owns task intent, policy preview, approval, audit correlation, and the native workbench. Herdr is the authoritative execution runtime for terminal agents and owns their processes, panes, semantic state, waits, detach/reconnect, and supported native session references. An adapter translates between the vendor-neutral contract and a specific tool; it must not create a competing execution state machine.

Local adapters use authenticated local transport. Process launches use an argument vector, explicit working directory, bounded environment allowlist, and product-generated correlation ID. Credentials, raw approval tokens, and unredacted prompts must not appear in command arguments, labels, status text, artifacts, or audit events.

## Required operation: discover

`discover` returns `AdapterIdentity`, declared capabilities, current `HealthEnvelope`, supported protocol versions, supported agent kinds, and the upstream executable/runtime fingerprint. A discovered executable is availability evidence only. It is not dispatch, health, authentication, or successful-agent proof.

## Required operation: dispatch

`dispatch` accepts a product task ID, correlation ID, agent kind, explicit working directory, immutable instruction reference or bounded instruction body, requested capabilities, environment-name allowlist, and policy-preview digest. It returns a stable run ID plus Herdr workspace/tab/pane identity when terminal-backed. External writes or cloud transmission require a matching, unexpired, one-shot approval before launch. Dispatch is idempotent for the same task/correlation/idempotency key and must reject a changed payload.

## Required operation: status

`status` reports the stable task ID, run ID, owner, authoritative runtime identity, revision, last transition time, and exactly one state: `queued`, `starting`, `running`, `blocked`, `succeeded`, `failed`, `cancelled`, `interrupted`, or `unknown`. Display metadata cannot override Herdr semantic agent state. `unknown` and lost transport are recovery conditions, never success.

## Required operation: handoff

`handoff` emits a versioned record containing task/run identity, source and destination owners, completed-history boundary, current state/revision, policy/audit correlation, artifact references, Herdr runtime identity, and an opaque native-session reference when one was authoritatively reported. A handoff never copies credentials and never claims that an active unfinished turn was captured unless the runtime proves it.

## Required operation: cancel

`cancel` targets the exact run and authoritative Herdr pane/process identity. It first requests graceful interrupt and reports `cancel_requested`; force termination is a separate policy level requiring explicit user approval when work or external state may be lost. Cancellation must be idempotent, persist the terminal state, and emit a correlated audit event. Closing the Forma AI window is not cancellation.

## Required operation: resume

`resume` requires a persisted interrupted/blocked/failed task record, its last accepted revision, the exact adapter/runtime fingerprint, and either a verified native-session reference or an explicit fresh-run decision. Stale, duplicated, unsupported, or mismatched session references fail closed. After reconnect, clients obtain a fresh Herdr snapshot, resubscribe to events, reconcile ownership/revision, and only then expose the task as resumed.

## Required operation: artifacts

`artifacts` returns bounded metadata: artifact ID, producing run ID, kind, product-relative or explicitly approved external path, size, digest, media type, ownership, created time, and validation state. The adapter never reads or publishes an artifact merely because a path was printed by an agent. External publication is a separate preview/approval/audit action.

## Required operation: audit

`audit` emits `AuditEnvelope` records correlated to task and run transitions. It records action, outcome, timestamp, adapter/runtime identity, policy-preview digest, approval reference where applicable, sizes/counts, error code, and explicit redacted-field names. It must not contain credentials, approval secrets, raw prompts, model output, or arbitrary provider/process error bodies.

## Compatibility and failure rules

- Protocol major-version mismatch fails closed before dispatch.
- Unknown response fields are ignored only within a compatible major version; missing required fields fail closed.
- Every mutating request carries task ID, run ID when allocated, correlation ID, expected revision, and idempotency key.
- Timeouts, disconnects, unknown state, blocked approval, and failed provider/runtime responses are not completion evidence.
- Adapter availability never makes Herdr optional for the core multi-agent loop.
- Semantica remains the governed long-term knowledge authority; handoff and status storage are operational task state only.

## Minimum conformance evidence

An adapter is not compatible until deterministic tests cover discovery, exact-payload dispatch, state transitions, blocked state, graceful and approved-force cancellation, reconnect reconciliation, native and fresh-run resume paths, artifact digest/ownership, redacted audit correlation, idempotency, revision conflicts, and protocol mismatch. A real terminal adapter additionally proves two parallel Herdr-backed fixture runs without cross-run input, state, artifact, or cancellation leakage.
