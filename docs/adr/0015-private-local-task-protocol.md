# ADR-0015: Private local task protocol

Status: accepted, 2026-08-30.

## Context

The installation assistant currently proves local inference with a hard-coded sample.
That is health evidence, not a daily product capability. The daily workbench needs to
submit arbitrary user text to the already authenticated local broker without exposing
the text in process arguments, shell history, routine audit, or diagnostics.

This first contract must not silently turn a failed local request into a cloud request.
Cloud escalation remains the separate preview and one-shot approval protocol in
ADR-0012.

## Decision

Add a versioned `local-task` Supervisor command and native-client method:

1. The native app sends a small JSON task body through the Supervisor child's standard
   input. User text never enters command-line arguments or environment variables.
2. Version 1 accepts one non-empty user prompt and an explicit output-token ceiling.
   It is intentionally narrower than the internal model API.
3. Supervisor requires the managed runtime to be healthy, discovers the active local
   model through the authenticated loopback broker, and submits a non-streaming request.
4. The response declares `route=local`, model, correlation ID, output, finish reason,
   token usage when available, and the redacted audit path.
5. The broker audit remains body-free. Supervisor does not add prompt or result bodies
   to routine logs or audit.
6. Empty/oversize input, malformed JSON, unhealthy runtime, unavailable model, timeout,
   broker rejection, malformed response, and empty output are distinct failures at the
   product boundary. None creates or sends a cloud request.
7. Provider-native tool calls are not accepted in this v1 local text contract. Real
   tools will use the separate governed tool proposal and approval pipeline.

## Initial limits

- Maximum Supervisor input: 1 MiB.
- Maximum prompt UTF-8 size: 256 KiB.
- Maximum output ceiling: 4,096 tokens.
- Non-streaming request with thinking disabled for the first interactive acceptance
  loop, so the UI receives one bounded result and cancellation semantics stay honest.

## Evidence required

- Input appears on standard input but not arguments, environment, or audit.
- A real reused Qwen model returns a non-empty result through the frozen Supervisor.
- Runtime stopped, local HTTP failures, malformed responses, and oversize bodies fail
  without producing a cloud proposal or outbound network request.
- The native client decodes and correlates the result and refuses oversize input before
  spawning Supervisor.

