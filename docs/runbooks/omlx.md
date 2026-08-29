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

## Upstream risk carried into our policy

Upstream reports show that status/model endpoints can remain responsive while actual generation is wedged. The deep probe exists to detect that class of failure. It is not a substitute for sustained-load, cancellation, memory-pressure, or restart testing.
