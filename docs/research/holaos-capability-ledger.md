# holaOS Capability and Reuse Ledger

Verified: 2026-08-31 Asia/Shanghai

This ledger is an upstream-source map, not integration acceptance. It records what Forma AI may evaluate for reuse before writing product-owned equivalents. No holaOS checkout, build, runtime, or adapter has been verified locally yet.

## Evidence snapshot

- Canonical repository: `holaboss-ai/holaOS`
- Reviewed revision: `4684714ee133794cdbb86630e42b7d93447fb2e2` on `main`
- Revision date reported by the official repository API: 2026-08-21
- Repository shape: Bun/Turbo workspaces with `apps/*`, `packages/*`, and independent services under `runtime/*`
- Runtime baseline: Node `24.14.1` is pinned by the upstream setup files; Electron and native SQLite/image dependencies are present
- GitHub's license classifier reports `NOASSERTION`; the repository's own `LICENSE` text is therefore authoritative for this review

The moving `main` branch and `latest` release are discovery references only. Any source acquisition or adapter compatibility claim must bind this full commit or a later separately reviewed immutable revision.

## License and distribution boundary

The upstream file describes a modified Apache 2.0 license. Its material additions are:

1. General commercial use is allowed, but using the source to provide a hosted service to third parties, or embedding it in a commercially distributed product or service, requires written authorization or a commercial license.
2. Internal use within one organization does not require that commercial license.
3. The frontend logo and copyright notices may not be removed or modified. The license defines the frontend as the components under `desktop/` when running source or the packaged desktop application.
4. The frontend-specific restriction does not apply to uses that do not involve the frontend; the remaining rights and obligations follow Apache 2.0 as modified by the file.

Decision for the current personal learning phase: inspect and reuse eligible non-visual implementation behind a separable adapter, retaining required notices and change records. Personal or non-commercial use does not erase license obligations.

Decision for future public distribution: do not ship holaOS frontend, logos, visual assets, or copied UI; do not embed holaOS source in a commercially distributed Forma AI build without written clearance. Before any public package, repeat legal/source review against the exact shipped revision and decide between separately installed adapter, clean-room compatible protocol, written authorization, or exclusion.

This is an engineering interpretation, not legal advice.

## Granular capability map

Status meanings: `reuse_candidate` means an exact upstream entry point exists but is not locally validated; `reference_only` means preserve capability parity without copying the implementation; `exclude` means outside the current product boundary.

| Capability | Official upstream evidence | Decision | Forma AI boundary and required validation |
|---|---|---|---|
| Local API service | `runtime/api-server` | reuse_candidate | Evaluate as a separately versioned service behind the Forma adapter. Verify loopback binding, authentication, permissions, cancellation, error envelopes, and shutdown before selection. |
| Agent harness hosting | `runtime/harness-host` | reuse_candidate | Evaluate its process/session lifecycle before building any substitute. Herdr remains the authoritative multi-agent executor; holaOS harness code may supply compatible tool or agent hosting only where roles do not conflict. |
| Agent harness implementations | `runtime/harnesses` | reuse_candidate | Map Codex, Claude, and built-in harness entry points at file level after pinned acquisition. Require dispatch, streaming status, interrupt, resume, artifact, and audit compatibility tests. |
| Persistent runtime state | `runtime/state-store` plus upstream history-pagination and memory-guard source tests | reuse_candidate | Reuse only for operational/session state. It must not become a second governed long-term memory authority; confirmed knowledge and decisions belong to Semantica. Test schema migration, crash recovery, pagination, and deletion. |
| Messaging/channel bridge | `runtime/channel-gateway`; README lists Slack, Feishu, DingTalk, and WeChat surfaces | reuse_candidate | Keep disabled by default. Each connector needs separate credential, data-egress, permission-preview, approval, audit, and distribution review. README breadth is not proof that each connector currently works. |
| Runtime client contract | `packages/runtime-client` | reuse_candidate | Prefer the upstream client over duplicating its transport after API-version compatibility and failure semantics are verified. Wrap it in the vendor-neutral Forma adapter contract. |
| Remote API contract | `packages/remote-api` | reuse_candidate | Inspect for reusable schemas/client behavior. Do not enable hosted dependencies or external writes without explicit product policy and user approval. |
| Interactive app host | `packages/app-host` | reuse_candidate | Evaluate non-visual host/lifecycle code for sandboxed app surfaces. Forma AI owns the native window, navigation, permissions, and review experience. |
| App protocol and SDK | `packages/app-sdk` and `packages/app-builder-sdk` | reuse_candidate | Reuse protocol/types/tooling where the exact license boundary permits. Add compatibility fixtures before allowing third-party apps. |
| Rich editor | `packages/editor` | reference_only | Preserve editing and artifact-interaction capability, but do not import it until a source-level license/dependency review proves it is separable from the restricted frontend. Native Forma AI UI remains product-owned. |
| Shared UI components | `packages/ui` | exclude | Do not copy, rebadge, bundle, or use as the Forma AI visual layer. Capability parity is required; visual identity and macOS implementation are independent. |
| Desktop product | `apps/desktop` | reference_only | Use behavior and workflow coverage as a reference. Do not redistribute its frontend, logos, assets, or branded shell without written clearance. |
| MCP, skills, integrations, browser, office/media tools, scheduled automation | Official README capability descriptions; exact implementation locations not yet proven in this bounded review | reference_only pending source map | These are parity requirements, not permission to reimplement immediately. After pinned source acquisition, locate each entry point and record reuse, adapter, or evidenced gap before coding. |
| BYOK and model/provider routing | Official README describes OpenAI, Anthropic, and compatible-provider keys plus built-in models | reference_only pending source map | Forma AI owns Keychain storage, credential state, preview, explicit approval, redacted audit, and local-first routing. Reuse provider plumbing only after secret-flow inspection and tests. |
| Shared memory | Official README and runtime memory-guard test | limited reuse_candidate | Allow transient conversation/session utilities only. Disable or redirect durable knowledge promotion through Semantica governance. |
| Hosted services, marketplace/hub, upstream accounts or wallets | README describes HolaHub and hosted ecosystem surfaces | exclude | No product dependency, production account, or external write is approved. A later connector task must define consent, data handling, and availability boundaries. |

## Upstream-first stop gate

Before implementing any holaOS-parity capability, the executing task must add a row or refine a row here with:

- exact pinned source path and revision;
- callable or importable entry point;
- relevant license/notice obligation;
- compatibility and security findings;
- decision: direct reuse, adapter reuse, reference only, or product-owned gap;
- a test that distinguishes upstream availability from successful Forma AI integration.

If an eligible non-visual implementation exists and can satisfy the adapter/security contract, duplicating it is a drift stop condition. If reuse is rejected, the evidence-backed reason must be license, compatibility, security, maintainability, or a demonstrated capability gap—not visual preference.

## Open validation gaps

- No immutable local checkout or archived source digest has been acquired.
- No upstream dependency install, build, unit test, runtime launch, or adapter smoke test has run.
- Exact file-level entry points for MCP, provider routing, browser automation, integrations, skills, scheduling, and the individual agent harnesses remain to be mapped from an acquired pinned tree.
- The relationship between `apps/desktop` and the license's `desktop/` wording requires explicit clearance before any frontend-related reuse.
- No compatibility claim exists yet for Herdr ownership of execution versus holaOS harness hosting.
- No public-distribution permission has been obtained.

## Primary sources

- [Repository at reviewed commit](https://github.com/holaboss-ai/holaOS/tree/4684714ee133794cdbb86630e42b7d93447fb2e2)
- [README at reviewed commit](https://github.com/holaboss-ai/holaOS/blob/4684714ee133794cdbb86630e42b7d93447fb2e2/README.md)
- [License at reviewed commit](https://github.com/holaboss-ai/holaOS/blob/4684714ee133794cdbb86630e42b7d93447fb2e2/LICENSE)
- [Root package manifest at reviewed commit](https://github.com/holaboss-ai/holaOS/blob/4684714ee133794cdbb86630e42b7d93447fb2e2/package.json)
- [Runtime tree](https://github.com/holaboss-ai/holaOS/tree/4684714ee133794cdbb86630e42b7d93447fb2e2/runtime)
- [Packages tree](https://github.com/holaboss-ai/holaOS/tree/4684714ee133794cdbb86630e42b7d93447fb2e2/packages)
