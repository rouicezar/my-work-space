# ADR 0003: oMLX Process Security Boundary

Status: accepted for prototype implementation, 2026-08-29.

## Context

The signed oMLX `v0.6.3` application passed artifact and shallow runtime checks, but a real launch with an explicit temporary `--base-path` still created `~/.omlx/bin/omlx-cluster-python`. The server also reported wildcard CORS origins. Upstream history shows that a CORS configuration field alone is not sufficient evidence that browser enforcement is active.

## Decision

- Launch oMLX with a product-owned process specification rather than inheriting the interactive user's environment.
- Set `HOME`, `XDG_CACHE_HOME`, `HF_HOME`, and `TMPDIR` to component-specific paths under product Application Support.
- Also pass explicit base, model, host, port, cache, and memory-guard arguments. Environment isolation and CLI paths are independent layers.
- Reject non-loopback bind addresses and privileged ports before process creation.
- Obtain `OMLX_API_KEY` from Keychain at spawn time. Never place the value in the manifest, arguments, journal, diagnostics, or serializable process specification.
- Do not expose the upstream HTTP server directly to a browser UI. The product-owned broker will authenticate and authorize callers, forward only supported routes, apply its own origin policy, rate limits, body limits, and audit correlation.
- Keep `isolation_contract` failed and `cors_contract` pending until the exact packaged build passes an adversarial real-process test.

## Required verification before promotion

1. Start the pinned oMLX build through the product launcher with a fresh isolated root.
2. Prove that no paths outside that root change, including the real user's home directory.
3. Prove non-loopback binding is impossible through every supported configuration surface.
4. Prove direct unauthenticated requests and disallowed browser origins cannot reach inference.
5. Prove the broker passes authenticated health, model-list, cancellation, streaming, and deep-inference traffic with a correlation ID.

## Consequences

The upstream process may continue to use its own home-relative conventions without contaminating the user's actual home. A product broker adds implementation and latency, but creates one stable security, audit, and compatibility boundary instead of depending on upstream CORS behavior.

## Upstream references

- [Issue #17: configured CORS origins were not applied as middleware](https://github.com/jundot/omlx/issues/17)
- [Issue #928: wildcard CORS default security report](https://github.com/jundot/omlx/issues/928)
