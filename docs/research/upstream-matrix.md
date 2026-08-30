# Upstream Compatibility Matrix

Verified: 2026-08-28. Sources are official repositories, release metadata, and build manifests. This is an engineering snapshot, not a promise that future releases remain compatible.

## Local source and pin inventory

Verified: 2026-08-31. Search boundaries were the Forma AI repository, the prior four-project research workspace under `~/Documents/Codex/2026-08-28`, normal user/system Applications folders, and product-managed Application Support paths. This is not a claim that no copy exists elsewhere on the machine.

| Component | Declared product pin | Local checkout/source result | Installed artifact result | Gap before reuse work |
|---|---|---|---|---|
| Semantica | `v0.6.7` in `config/upstreams.json` and `config/product-manifest.json` | No Git checkout found. The directory named `ai-memory-semantica` contains only empty `outputs/` and `work/` directories and is not a repository. | No managed Semantica runtime was found in the searched product paths. | Acquire or locate the exact `v0.6.7` wheel/source archive and record its digest before source-level capability mapping. |
| holaOS | rolling `latest` in both manifests; this is not an immutable pin | No local checkout found in the searched repository/research workspace. | No installed holaOS application found in normal Applications or product-managed paths. | Resolve an immutable commit for the current personal-development source review; do not treat `latest` or `main` as reproducible evidence. |
| Herdr | `v0.8.2` in both manifests | No local checkout found in the searched repository/research workspace. | No installed Herdr binary/application found in the searched product or Applications paths. | Acquire or locate the exact `v0.8.2` source/release artifact and record checksum plus protocol surface before integration. |
| oMLX | `v0.6.3` in both manifests | No local source checkout found. | Verified product-managed `oMLX.app` exists at the legacy pre-Forma support root; bundle ID `app.omlx`, short version `0.6.3`, build `2500`. Its active record binds SHA-256 `5bde65e35c0cc3e7b0365c0e078f98d7571cb71c6a6bead591329a2cf8287537`. | Treat the installed app as binary/runtime evidence, not source evidence; add a migration task for the legacy support-root name and locate pinned source only if source-level reuse becomes necessary. |

Repository-local integration code currently exists only for Semantica and oMLX adapters. No repository-local holaOS or Herdr adapter exists yet. That absence is an integration gap, not permission to reimplement their upstream capabilities.

| Component | Stable reference | Runtime/platform | Product interface | Official distribution evidence | Current integration conclusion |
|---|---|---|---|---|---|
| Semantica | `v0.6.7`, annotated tag targets commit `ecb33a5b7d1c232da77527da89d861e2b10e9c42` | Python `>=3.8`; project labels OS-independent | Python library, five CLI entry points, REST server, worker, Explorer, stdio MCP | Wheel SHA-256 `94786f20cd2c91144247d78c1baa2256160709c2fe6c332118c1f95d80232204`; sdist SHA-256 `c32ab9ae2829284e2cc109829ab7fd3497ce8912d2302f198ab583f4af790d58` | Reuse the pinned library surface inside a product-managed environment; expose product governance through a thin adapter and use MCP selectively for external compatible agents |
| holaOS | rolling `latest` release, source on `main` | Node `>=24`; `.nvmrc` pins `24.14.1`; Electron; README claims macOS Apple Silicon and Intel, Windows, Linux | Desktop UI, local runtime, MCP and agent workspace | Latest release contains no binary assets; official OSS path clones/builds source | Treat as an externally installed, version-fingerprinted adapter until license and reproducible binary distribution are resolved |
| Herdr | `v0.8.2` | Single Rust binary; official macOS arm64 and x86_64 assets | CLI and socket/API-oriented agent terminal control | Versioned binaries for macOS, Linux, Windows | Pin the macOS arm64 binary for first Apple Silicon release; verify checksum, protocol, update channel, state path, detach/reconnect |
| oMLX | `v0.6.3` | macOS 15+; Apple Silicon; Python `>=3.11,<3.14` for source; official app includes runtime | OpenAI-compatible HTTP API at `/v1`; CLI; admin UI; native menu-bar app | Versioned DMGs for macOS 15 and macOS 26–27 plus CPython 3.11–3.13 wheels | Prefer verified official DMG acquisition for the initial product; adapter owns health/routing while upstream app owns its runtime/update until lifecycle tests justify rebundling |

## Material compatibility findings

### Semantica

- The `v0.6.7` package declares MIT and exposes `semantica`, `semantica-server`, `semantica-worker`, `semantica-explorer`, and `semantica-mcp` entry points. Its annotated tag object is unsigned and the GitHub release metadata reports `immutable: false`; Forma AI must bind the target commit and release-asset digest rather than trust the tag name alone.
- The official CLI guide says the REST server binds to port 8000 by default and MCP uses stdio. oMLX also defaults to port 8000, so the product must assign and persist non-conflicting ports rather than accept upstream defaults.
- Its base dependency set is large, including Torch, FAISS, ONNX Runtime, document and media libraries. Most runtime dependencies use minimum-version ranges rather than an exact lock. A separate managed environment and a Forma AI-reviewed lock are required; sharing oMLX's Python runtime would undermine reproducibility.
- `AgentContext` already provides store, retrieve, forget, conversation, save/load, decision recording, precedent lookup, causal-chain analysis, policy access, GraphRAG expansion, and graph analytics. Forma AI must reuse those capabilities rather than build a parallel memory/decision engine.
- The release also includes provenance, ontology/reasoning, export, pipeline parallelism, ContextGraph persistence, LangChain integration, and provider integrations. These are upstream capability candidates and require explicit ledger decisions before any product-owned equivalent is implemented.

#### Semantica reuse boundary for Forma AI

| Capability | Upstream surface to reuse | Forma AI responsibility | Current evidence status |
|---|---|---|---|
| Confirmed memory content and lifecycle | `semantica.context.AgentContext` store/get/retrieve/forget/save/load | Candidate/confirmation policy, approval state, correlation, redacted audit, and fail-closed service boundary | Contract-tested locally; real managed runtime and approved embedding route remain pending |
| Decisions and causal evidence | `AgentContext` decision, precedent, causal-chain, explainability, and policy surfaces | Decide which task events become governed decisions and validate provenance before promotion | Mapped from pinned source; not yet integrated end to end |
| Knowledge graph, provenance, reasoning, export | ContextGraph, provenance manager, ontology/reasoning/export modules | Capability exposure, permission policy, artifact validation, and UI review | Available upstream; product reuse decision pending per surface |
| External agent access | `semantica-mcp` stdio and versioned Python/CLI surfaces | Authenticate/isolate invocation, declare capabilities through the Forma agent adapter, and correlate audits | Official entry point verified; MCP runtime contract not yet tested in Forma AI |
| REST/Explorer | Upstream server and Explorer | Do not expose as the product authority by default; place behind authenticated loopback/product policy if later needed | Not selected for the current governed-memory path |
| Embeddings/vector index | Semantica vector interfaces plus Forma AI's verified oMLX embedding route | Select and approve exact local embedding model, bind dimension/model revision, and validate real inference | Product adapter exists; production embedding model remains unapproved |

The product-owned governed envelope is an integration and policy layer, not a replacement memory implementation. Raw task input and unconfirmed candidates remain outside Semantica; confirmed sourced knowledge and decision evidence are written through the pinned Semantica authority.

### holaOS

- The repository requires Node 24 and uses Bun/Electron workspaces, native SQLite-related dependencies, and a prepared runtime bundle.
- The official `latest` release is not a semantic version and has no release assets. A branch-moving install cannot satisfy our reproducibility or rollback requirements without pinning a commit and independently building/verifying artifacts.
- holaOS also has its own shared memory. The adapter must disable or limit that layer to transient UI/session state so Semantica remains the governed authority.

### Herdr

- The canonical repository is now `herdrdev/herdr`; older `ogulcancelik/herdr` URLs redirect and should not remain in product configuration.
- Stable and preview channels exist. The product must pin stable and suppress uncoordinated self-update until compatibility tests approve a new version.
- The official arm64 asset is approximately 18 MB, making a verified binary integration feasible.

### oMLX

- The `v0.6.3` tag is a lightweight tag resolving directly to commit `85708e4b9a585df42241c826b6be2b4dba018406`. GitHub reports the release as stable but `immutable: false`, so product acquisition binds exact artifact size and SHA-256 rather than the release label alone.
- Official v0.6.3 artifacts include CPython 3.11, 3.12, and 3.13 universal2 wheels plus separate macOS 15 and macOS 26–27 DMGs. The selected macOS 26–27 DMG is `807057789` bytes with SHA-256 `5bde65e35c0cc3e7b0365c0e078f98d7571cb71c6a6bead591329a2cf8287537`; this matches the installed product-managed artifact record.
- The pinned `pyproject.toml` declares Apache-2.0, Python `>=3.11,<3.14`, MLX `0.32.0`, commit-pinned `mlx-lm`, `mlx-embeddings`, and `mlx-vlm`, and several ABI-coupled/custom-kernel dependencies. Forma AI must use the official verified app/runtime or reproduce the entire pinned build contract; a casual shared Python environment is not compatible evidence.
- The pinned server exposes `GET /health`, authenticated `GET /v1/models`, `POST /v1/completions`, `POST /v1/chat/completions`, `POST /v1/messages`, `POST /v1/responses`, `POST /v1/embeddings`, `POST /v1/rerank`, model load/unload/status routes, and optional MCP/audio/web-search surfaces. Forma AI's initial broker intentionally exposes only health, model listing, and chat completion; the other routes require separate capability, security, and approval decisions.
- `/health` can report startup/loading state and is deliberately unauthenticated upstream; `/v1/models` proves discovery, not generation. A route's existence also does not prove a compatible model is installed. Readiness remains layered: process/HTTP, health, model discovery, then an actual bounded inference response tied to the requested model ID.
- Real local evidence now exists for chat generation: pinned oMLX v0.6.3 plus file-verified `mlx-community/Qwen3-0.6B-4bit` revision `73e3e38d981303bc594367cd910ea6eb48349da8` returned HTTP 200, non-empty output, finish reason `stop`, and token usage through the Forma broker. The output differed slightly from the requested exact string, so this proves inference, not strict instruction compliance.
- `POST /v1/embeddings` exists upstream, but the current Qwen model is a causal LLM and is catalogued only for `chat`. No embedding capability may be inferred from the route alone. Semantic retrieval remains unavailable until a separately pinned, approved embedding model completes a real call with verified model ID, dimension, restart, and ownership behavior.
- Real-runtime streaming, cancellation, memory pressure, sustained concurrency, restart recovery, updater ownership, complete filesystem auditing, and an approved embedding call remain open release gates.
- Official docs require macOS 15+ and Apple Silicon and publish separate large DMGs for macOS 15 versus macOS 26–27.
- The macOS app has its own auto-update and CLI shim. Our lifecycle design must choose one update owner; two independent updaters would break version pinning and rollback.
- The source build contains commit-pinned inference dependencies and optional native kernels. Rebuilding without the full Metal toolchain can silently produce much slower paths, so the initial product should prefer official signed artifacts and explicitly verify kernel/capability status.

## Cross-component blockers

1. **Port collision:** Semantica REST and oMLX both document port 8000 defaults.
2. **Update ownership:** Herdr and oMLX support their own update mechanisms, while reproducible product releases require a coordinated manifest.
3. **Runtime separation:** Semantica's broad Python dependency graph should not share oMLX's tightly pinned runtime.
4. **Memory authority:** holaOS shared memory overlaps Semantica and requires a strict transient/confirmed boundary.
5. **holaOS distribution:** current licensing and absence of release binaries prevent treating it like the other three bundle candidates.

## Primary sources

- [Semantica v0.6.7 release](https://github.com/semantica-agi/semantica/releases/tag/v0.6.7), [package manifest](https://github.com/semantica-agi/semantica/blob/v0.6.7/pyproject.toml), [CLI setup](https://github.com/semantica-agi/semantica/blob/main/docs/cli-setup.md)
- [holaOS repository](https://github.com/holaboss-ai/holaOS), [package manifest](https://github.com/holaboss-ai/holaOS/blob/main/package.json), [license](https://github.com/holaboss-ai/holaOS/blob/main/LICENSE), [latest release](https://github.com/holaboss-ai/holaOS/releases/tag/latest)
- [Herdr v0.8.2 release](https://github.com/herdrdev/herdr/releases/tag/v0.8.2), [package manifest](https://github.com/herdrdev/herdr/blob/v0.8.2/Cargo.toml), [license](https://github.com/herdrdev/herdr/blob/v0.8.2/LICENSE)
- [oMLX v0.6.3 release](https://github.com/jundot/omlx/releases/tag/v0.6.3), [package manifest](https://github.com/jundot/omlx/blob/v0.6.3/pyproject.toml), [installation requirements](https://github.com/jundot/omlx#install), [packaging notes](https://github.com/jundot/omlx/blob/main/packaging/README.md)
