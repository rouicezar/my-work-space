# oMLX v0.6.3 macOS 26 Artifact and Shallow Runtime Evidence

Date: 2026-08-29  
Environment: Apple Silicon, macOS 26.6.2  
Scope: official artifact integrity, macOS trust, empty-model startup, shallow HTTP contract, graceful shutdown, and isolation observation.

## Artifact

- Release: `v0.6.3`
- Asset: `oMLX-0.6.3-macos26-27.dmg`
- Expected and actual size: `807057789` bytes
- Expected and actual SHA-256: `5bde65e35c0cc3e7b0365c0e078f98d7571cb71c6a6bead591329a2cf8287537`
- Result: size and digest match.

## Mounted application

- Bundle identifier: `app.omlx`
- Short version: `0.6.3`
- Build: `2500`
- Minimum macOS: `15.0`
- Architectures: `x86_64`, `arm64`
- Deep code-sign verification: passed
- Signing identity: Developer ID Application, Team ID `PSK5Q5T46L`
- Gatekeeper: accepted as Notarized Developer ID
- Result: application trust checks passed.

## Isolated runtime attempt

The app was not copied to `/Applications`. The bundled `omlx-cli` ran from the read-only mounted image with:

- explicit temporary base path;
- explicit empty model directory;
- loopback host;
- test port `18000`;
- Hugging Face cache discovery disabled;
- oMLX cache disabled;
- safe memory guard.

Observed:

- server reached application-startup complete;
- version banner reported `0.6.3` and macOS 26–27 build;
- zero models were discovered;
- `GET /health` returned `status: healthy`, no default model, zero loaded models;
- `GET /v1/models` returned an empty OpenAI-compatible data list;
- product adapter returned `healthy_no_models`;
- SIGINT produced graceful application and engine-pool shutdown.

## Failed or incomplete gates

### Isolation failed

Despite the temporary `--base-path`, the process created `~/.omlx/bin/omlx-cluster-python`, pointing into the mounted application runtime. The exact new link and its newly empty parent directories were removed after shutdown. The product must not claim project-local isolation until a wrapper or upstream option prevents this write and a regression test proves it.

### CORS policy requires correction

Startup logged wildcard CORS origins. Public product defaults must restrict access to required loopback/UI origins and prove unauthorized origins are rejected.

### Deep inference is pending

No model was downloaded. Tool calling, embeddings, reranking, real generation, timeout recovery, cancellation, memory pressure, restart, and sustained concurrency remain unverified.

## Cleanup

- Service stopped gracefully.
- Unintended user-home symlink and empty directories removed.
- DMG detached.
- Temporary runtime, mount directory, and downloaded DMG removed.
