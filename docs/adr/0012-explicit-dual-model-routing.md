# ADR-0012: Explicit dual-model routing

Status: accepted, 2026-08-30.

## Context

The product must remain useful on ordinary Apple Silicon Macs without making every
task or private document a cloud request. The existing local route uses Qwen through
oMLX. Some tasks will exceed a tested local profile because of context length,
modality, tool-schema support, resource pressure, or required result quality.

DeepSeek is the first requested cloud provider. Its official API is compatible with
the OpenAI API format, but its supported model identifiers, features, concurrency,
and prices change independently of this application. On 2026-08-30 the official
models page lists `deepseek-v4-flash`, `deepseek-v4-pro`, and an experimental vision
variant at `https://api.deepseek.com`; it also states that prices can change.

## Decision

Use a product-owned, replaceable inference-router contract:

1. Local Qwen through oMLX is always considered first and is the only enabled route
   after installation.
2. Eligibility is determined from a versioned task contract and tested model profile:
   required modality, estimated context, tool interface, local health/resources, and
   an explicit result validator. Model self-assessment is not authoritative.
3. When local execution is ineligible or its output fails validation, create a cloud
   escalation proposal. Creating the proposal performs no cloud request.
4. Each proposal displays the reason, exact data classes and redactions, outbound
   payload digest, provider/model, output ceiling, price-source timestamp, estimated
   cost range or an honest cost-unknown state, privacy implications known to the
   product, side effects, and cancellation behavior.
5. A one-shot approval is bound to the proposal digest, provider, model, limits,
   correlation ID, and expiry. The adapter verifies the digest again immediately
   before transmission. Any change invalidates approval.
6. The DeepSeek key is stored in macOS Keychain. It is injected only into the HTTPS
   request and never persisted in arguments, files, UI state, audit, logs, or exports.
7. Cloud output cannot directly execute a tool. Tool calls are normalized into
   proposals and pass through the same product tool-policy and approval boundary.
8. Audit stores routing decisions, manifest/digest, approval outcome, provider/model,
   timing, response classification, token usage, price snapshot, and computed cost;
   it does not store credentials or prompt/response bodies by default.
9. Provider/model/capability/price data lives in a signed, versioned provider catalog.
   Application code targets the adapter contract, not a permanent DeepSeek model ID.
10. Denial, cancellation, authentication, balance, rate limit, overload, timeout,
    content filter, incompatible response, validation failure, and cost uncertainty
    are distinct outcomes. None silently selects another model or provider.
11. The DeepSeek preview discloses the provider policy's stated processing/storage in
    the People's Republic of China, its non-fixed retention language, and the user's
    responsibility for data they choose to transmit. Provider training opt-out is
    shown as a separate account setting whose state is unknown until independently
    verified. Credentials and designated sensitive data classes are blocked from the
    first cloud route rather than relying on a warning alone.

## Initial DeepSeek protocol

- HTTPS origin: `https://api.deepseek.com` only.
- Initial transport: non-streaming Chat Completions, minimizing parser and partial
  billing ambiguity for the first acceptance loop.
- Authentication: bearer API key from Keychain.
- Model availability: verified through the provider models endpoint before enabling a
  catalog selection.
- Usage: normalized from the provider response and used for post-run cost accounting.
- Provider HTTP classifications include 400, 401, 402, 422, 429, 500, and 503 plus
  transport timeout and invalid JSON/shape.

Streaming, vision, provider-hosted file storage, beta endpoints, and provider-native
tools are outside the first cloud acceptance loop. They require separate data-route
and cancellation designs.

## Consequences

This adds an explicit approval step before cloud work and may leave some tasks
unfinished when price data or provider health cannot be verified. That friction is
intentional: local-first is a privacy and control property, not merely a preference.
The adapter boundary allows another provider to be added without changing the task,
approval, or audit contracts.

## Evidence required

- Contract tests for local eligibility and every escalation reason.
- Proof that proposal creation is offline and that denial sends zero bytes.
- Exact serialized-payload digest verification at transmission time.
- Keychain round trip and secret-free process arguments, logs, audit, and diagnostics.
- DeepSeek response and HTTP failure normalization using synthetic fixtures.
- One real, low-cost DeepSeek request after the user configures a test key and approves
  the displayed payload and ceiling.
- Cancellation, stale-price, usage/cost reconciliation, and provider-disable tests.
- Privacy-preview tests against the pinned effective policy metadata, including
  blocked sensitive classes and an honest unknown opt-out state.

Official sources consulted on 2026-08-30:

- https://api-docs.deepseek.com/
- https://api-docs.deepseek.com/quick_start/pricing/
- https://api-docs.deepseek.com/quick_start/error_codes/
- https://api-docs.deepseek.com/api/create-chat-completion/
- https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html
- https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html
