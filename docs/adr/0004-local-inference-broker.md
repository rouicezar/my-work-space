# ADR 0004: Product-Owned Local Inference Broker

Status: accepted for prototype implementation, 2026-08-29.

## Context

The product cannot safely expose oMLX directly to browser content or depend on its CORS implementation as the authorization boundary. It also needs one stable place to enforce request policy and correlate inference with the end-to-end audit trail while keeping oMLX replaceable.

## Decision

The native product owns a loopback-only inference broker between all callers and oMLX.

- The broker and oMLX each use a different random bearer token sourced from Keychain at runtime.
- Only `GET /health`, `GET /v1/models`, and `POST /v1/chat/completions` are initially forwarded.
- Query strings, unknown routes and wrong methods fail closed.
- Browser origins use an exact allowlist. Native callers without an `Origin` header still require authentication.
- Preflight allows only the route's known method and `Authorization`, `Content-Type`, and `X-Correlation-ID` headers.
- Request bodies have a hard size limit and POST bodies must be JSON objects.
- Caller headers are not forwarded. The broker constructs upstream authentication and correlation headers itself.
- Responses use `Cache-Control: no-store`; every decision receives or creates a bounded correlation ID.
- Audit records contain metadata and outcomes, not authorization values or request/response bodies.
- Total upstream requests and inference requests have separate non-blocking concurrency gates. Health remains available while inference slots are occupied, unless the independent total gate is exhausted.
- Inference requests use a sliding one-minute rate gate. Rejections return `429` or `503` with a bounded retry hint and an explicit audit outcome.
- Request and response bodies have independent byte limits. The upstream transport reads at most `limit + 1` bytes, so an oversized response is not fully buffered.
- Upstream timeout, unavailability, oversized response and invalid content type are distinct failures. API responses use `nosniff` and only JSON is accepted in the current non-streaming contract.
- Requests asking for streaming fail explicitly until streaming cancellation and backpressure are implemented.

## Current boundary

The prototype buffers complete bounded JSON responses. Streaming, cancellation propagation, per-caller identity quotas, connection shutdown and real-model pressure tests are still required before deep inference can be promoted to release-ready. Current admission and size limits are safe development defaults, not performance claims; supported hardware profiles must tune and validate them.

## Consequences

UI and agent code target a product contract rather than an upstream implementation. Replacing oMLX becomes an adapter change. The broker is security-sensitive and therefore requires adversarial tests and independent review before release.
