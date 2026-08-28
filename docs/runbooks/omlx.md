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

The adapter contract is covered by deterministic simulated responses. On the current development Mac, neither the oMLX app nor CLI was found and port 8000 was not listening. Therefore `config/product-manifest.json` correctly retains `pending-adapter-verification`; no real artifact, start/stop, model, or inference evidence exists yet.

## Upstream risk carried into our policy

Upstream reports show that status/model endpoints can remain responsive while actual generation is wedged. The deep probe exists to detect that class of failure. It is not a substitute for sustained-load, cancellation, memory-pressure, or restart testing.
