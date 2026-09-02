# Herdr v0.8.2 P3-T12 Live-Test Diagnostic Hardening

Verified: 2026-09-02 Asia/Shanghai

## Scope

This correction changes only the P3-T12 live integration-test harness. It does not add a task runtime, alter Herdr state, or widen the provider-free fixture into real-model evidence.

## Changes

- Emit flushed elapsed-time stages for server start, socket readiness, pane readiness, each detected Agent, parallel completion, cancellation, isolation assertions, and cleanup.
- Capture the test-launched server output and print its final 40 lines on failure.
- Bound each socket request to 15 seconds, marker waits to 10 seconds, both Agent starts to 5 seconds, and each cleanup command to 10 seconds.
- Add a 45-second whole-test watchdog that names the last stage and includes the server-output tail.
- Treat nonzero or timed-out `session stop` / `session delete` cleanup as a test failure.

## Verification

- Initial live run: passed in 10.174 seconds with every stage visible.
- Consecutive stability run: 10 of 10 passed in 100.312 seconds; each run completed in approximately 9.8–10.2 seconds including cleanup.
- Focused Herdr transport/adapter/presentation/integration suite: 55 passed in 19.620 seconds.
- Full Python suite: 298 passed with 1 expected opt-in Semantica skip in 23.849 seconds.
- Swift package: 43 passed with 2 environment-gated Keychain skips.
- `git diff --check`: passed.
- No `forma-p3t12-*`, `forma-p3t13-*`, or `forma-p3t14-*` session directory remained after verification.

## Boundary

This establishes bounded and observable test behavior. It does not prove a real model-Agent loop, provider-native resume, runtime UI replacement, or user-task recovery. Those remain later gates.
