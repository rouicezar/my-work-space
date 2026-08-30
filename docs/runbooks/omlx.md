# oMLX Adapter Runbook

Adapter target: official oMLX `v0.6.3` on Apple Silicon macOS.

## Contract

The adapter uses:

- `GET /health` for HTTP/server startup state;
- `GET /v1/models` for OpenAI-compatible model discovery;
- `POST /v1/chat/completions` with at most two output tokens for an optional deep inference probe.

It does not treat an open port, a green `/health`, or a responsive model list as proof that inference works. `ready` requires a real, time-bounded completion. Deep probes consume local compute and are opt-in outside formal acceptance or watchdog policy.

## Status meanings

| Status | Meaning | User-facing action |
|---|---|---|
| `not_installed` | No app/CLI evidence and server unreachable | Offer verified installation flow |
| `stopped` | Installation found but HTTP unavailable | Offer start/retry and show logs |
| `starting` | Server reports loading/starting | Wait with bounded timeout |
| `auth_required` | Server is reachable but API authorization failed | Request/recover Keychain-backed credential |
| `incompatible` | Response shape or health semantics do not match contract | Stop and require adapter/version review |
| `healthy_no_models` | Server is healthy but no models are discoverable | Guide model download/selection |
| `shallow_ready` | HTTP health and model discovery pass | Do not claim inference verified |
| `degraded` | Shallow checks pass but real generation fails/times out | Block agent routing; offer restart/diagnostics |
| `ready` | A listed model completed the bounded deep probe | Permit local inference route |

## Developer command

```bash
python3 scripts/omlx_health.py
python3 scripts/omlx_health.py --deep --model MODEL_ID
```

API keys are read from the environment name supplied by `--api-key-env` (default `OMLX_API_KEY`) and are never accepted as command-line values. The product UI must retrieve the secret from Keychain and pass it to the adapter without logging it.

## Current evidence boundary

The adapter contract is covered by deterministic simulated responses and a real local HTTP transport test. The official `v0.6.3` macOS 26–27 DMG has also passed size, SHA-256, signature, notarization, version, architecture, isolated empty-model startup, shallow health, model-list, and graceful-stop checks on the development Mac.

No model has been downloaded, so deep inference remains unverified and the overall `health_contract` stays `pending-adapter-verification`.

The real startup also found two product blockers:

1. `--base-path /tmp/...` did not fully isolate state. oMLX still created `~/.omlx/bin/omlx-cluster-python`. The exact link and newly empty directories were removed after the test. A product wrapper must prove a fully isolated home/config strategy before installation is enabled.
2. The server logged CORS origins as `['*']`. The product must configure and test an explicit loopback/UI origin policy instead of accepting this default.

The accepted containment design is documented in [ADR 0003](../adr/0003-omlx-process-security-boundary.md). The process specification and product broker have passed a pinned-artifact shallow regression. The known `~/.omlx` write was redirected into the product HOME and the real user's `~/.omlx` remained absent. Full filesystem auditing and deep inference are still required before the isolation contract can be considered release-ready.

## Product inference broker prototype

`scripts/omlx_broker.py` is the runnable development entry for the loopback-only broker described in [ADR 0004](../adr/0004-local-inference-broker.md). The production launcher must obtain both tokens from Keychain and inject them only into the child environment:

- `FORMA_AI_BROKER_TOKEN`: authenticates native UI and agent calls to the broker;
- `OMLX_API_KEY`: a different token used only from broker to oMLX.

The entry requires an explicit `--audit-path`. Browser use additionally requires one or more exact `--allowed-origin` values. Do not place token values in arguments, configuration files, shell history, logs, or diagnostics.

The broker contract has passed synthetic tests and a real-loopback HTTP regression against the pinned oMLX artifact. See [the evidence record](../../evidence/upstream/omlx-v0.6.3-isolation-broker-2026-08-29.md). Synthetic gates now cover request/response bounds, total and inference concurrency, rate limiting, upstream timeout/unavailability, invalid content types and explicit streaming rejection. Real-model streaming, cancellation, pressure, and sustained-concurrency gates remain pending.

## Upstream risk carried into our policy

Upstream reports show that status/model endpoints can remain responsive while actual generation is wedged. The deep probe exists to detect that class of failure. It is not a substitute for sustained-load, cancellation, memory-pressure, or restart testing.
