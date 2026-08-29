# oMLX v0.6.3 Product-Home Isolation and Broker Evidence

Date: 2026-08-29  
Environment: Apple Silicon, macOS 26.6.2  
Artifact: official `oMLX-0.6.3-macos26-27.dmg`  
Scope: empty-model runtime, product-owned HOME containment and real loopback broker policy.

## Artifact gate

- Size: `807057789` bytes, exact match.
- SHA-256: `5bde65e35c0cc3e7b0365c0e078f98d7571cb71c6a6bead591329a2cf8287537`, exact match.
- The verified DMG was mounted read-only and the bundled `omlx-cli` was executed from the mount.

## Process environment

The process inherited no interactive environment. It received only product-owned `HOME`, `XDG_CACHE_HOME`, `HF_HOME`, `TMPDIR`, loopback `NO_PROXY`, a minimal system `PATH`, and an oMLX API key. CLI arguments supplied explicit base path, model directory, loopback host, test port, disabled upstream caches and the safe memory guard.

Observed:

- oMLX `0.6.3` started on `127.0.0.1:18000` with zero models.
- The known `~/.omlx/bin/omlx-cluster-python` write was contained under the temporary product HOME. In this run it was a small executable wrapper rather than a link.
- The real user's `~/.omlx` did not exist during the test.
- Open writable regular files reported by `lsof` were the isolated oMLX crash and server logs. No writable regular file under the real user HOME was observed.
- Graceful interrupt stopped the memory enforcer, downloaders, engine pool and server.

This is shallow containment evidence, not a complete filesystem-access proof. A release still requires a sandbox/file-event regression covering startup, inference, model management, updates and failure paths.

## Direct oMLX authentication

- `GET /health` returned `200` without authentication; this is upstream behavior.
- `GET /v1/models` returned `401` without the API key and `200` with the configured API key.
- The model list contained zero models.
- oMLX still logged wildcard CORS origins. The product therefore does not expose this port as its browser contract.

## Real product-broker chain

The product broker ran on `127.0.0.1:18110` and forwarded to the real oMLX process.

| Probe | Result |
|---|---:|
| Broker health without caller token | `401` |
| Broker health with caller token | `200` |
| Broker model list with caller token | `200` |
| Allowed exact browser origin | exact origin header returned |
| Disallowed browser origin | `403` |
| Unknown route | `404` |
| Allowed preflight | `204` |
| Disallowed-origin preflight | `403` |

The broker audit contained eight events spanning forwarded, authentication-denied, origin-denied, route-denied, preflight-allowed and preflight-denied outcomes. The supplied correlation ID appeared in the audit. The audit file mode was `0600`; neither caller nor upstream token appeared in it.

## Remaining gates

- No model was downloaded; generation, streaming and cancellation remain unverified against real oMLX.
- Full filesystem access auditing and macOS sandbox design remain pending.
- Response-size limits, rate limits, concurrent admission and abnormal upstream termination remain pending.
- Fixed development ports and tokens used for this test are not production defaults; production credentials must be random and Keychain-backed.
