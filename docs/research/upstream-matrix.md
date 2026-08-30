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
| Semantica | `v0.6.7` | Python `>=3.8`; project labels OS-independent | CLI, REST server, worker, Explorer, stdio MCP | Release wheel and source archive | Pin wheel in a product-owned Python environment; test REST/MCP contracts and local storage before bundling |
| holaOS | rolling `latest` release, source on `main` | Node `>=24`; `.nvmrc` pins `24.14.1`; Electron; README claims macOS Apple Silicon and Intel, Windows, Linux | Desktop UI, local runtime, MCP and agent workspace | Latest release contains no binary assets; official OSS path clones/builds source | Treat as an externally installed, version-fingerprinted adapter until license and reproducible binary distribution are resolved |
| Herdr | `v0.8.2` | Single Rust binary; official macOS arm64 and x86_64 assets | CLI and socket/API-oriented agent terminal control | Versioned binaries for macOS, Linux, Windows | Pin the macOS arm64 binary for first Apple Silicon release; verify checksum, protocol, update channel, state path, detach/reconnect |
| oMLX | `v0.6.3` | macOS 15+; Apple Silicon; Python `>=3.11,<3.14` for source; official app includes runtime | OpenAI-compatible HTTP API at `/v1`; CLI; admin UI; native menu-bar app | Versioned DMGs for macOS 15 and macOS 26–27 plus CPython 3.11–3.13 wheels | Prefer verified official DMG acquisition for the initial product; adapter owns health/routing while upstream app owns its runtime/update until lifecycle tests justify rebundling |

## Material compatibility findings

### Semantica

- The `v0.6.7` package declares MIT and exposes `semantica`, `semantica-server`, `semantica-worker`, `semantica-explorer`, and `semantica-mcp` entry points.
- The official CLI guide says the REST server binds to port 8000 by default and MCP uses stdio. oMLX also defaults to port 8000, so the product must assign and persist non-conflicting ports rather than accept upstream defaults.
- Its base dependency set is large, including Torch, FAISS, ONNX Runtime, document and media libraries. A separate managed environment is safer than sharing oMLX's Python runtime.

### holaOS

- The repository requires Node 24 and uses Bun/Electron workspaces, native SQLite-related dependencies, and a prepared runtime bundle.
- The official `latest` release is not a semantic version and has no release assets. A branch-moving install cannot satisfy our reproducibility or rollback requirements without pinning a commit and independently building/verifying artifacts.
- holaOS also has its own shared memory. The adapter must disable or limit that layer to transient UI/session state so Semantica remains the governed authority.

### Herdr

- The canonical repository is now `herdrdev/herdr`; older `ogulcancelik/herdr` URLs redirect and should not remain in product configuration.
- Stable and preview channels exist. The product must pin stable and suppress uncoordinated self-update until compatibility tests approve a new version.
- The official arm64 asset is approximately 18 MB, making a verified binary integration feasible.

### oMLX

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
