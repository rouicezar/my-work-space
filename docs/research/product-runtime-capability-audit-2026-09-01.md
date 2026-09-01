# Product-Owned Runtime Capability Audit (P1-T09)

Date: 2026-09-01
Scope: every product-owned runtime-like capability in `forma_ai/`, `scripts/supervisor.py`, `scripts/semantica_memory_runtime.py`, and the Swift runtime-path sources (`SupervisorProtocol.swift`, `RuntimeSecrets.swift`, `ProductManifest.swift`), audited against the four upstream capability ledgers and the P1 reuse decisions.
Method: full source read of every `forma_ai` source file (34 modules across the package root and `adapters/`) plus the two script entrypoints and the Swift runtime-path sources; each capability is assigned one disposition with file/line evidence, the relevant upstream entry point, license, and the owning downstream task. Verification commands cited per row were re-checked at the audited revision.

Upstream evidence sources:

- `docs/research/upstream-matrix.md` (oMLX v0.6.3, `85708e4b9a585df42241c826b6be2b4dba018406`, Apache-2.0; Semantica v0.6.7, `ecb33a5b7d1c232da77527da89d861e2b10e9c42`, MIT)
- `docs/research/herdr-capability-ledger.md` (Herdr v0.8.2, `9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c`, Apache-2.0)
- `docs/research/holaos-capability-ledger.md` (holaOS, `4684714ee133794cdbb86630e42b7d93447fb2e2`, modified Apache-2.0, external-install-only pending written clearance)
- `docs/research/license-matrix.md`, `docs/decisions.md` (ADR-004, ADR-017)

## Disposition taxonomy

- **Justified product-owned**: policy, orchestration, lifecycle, audit, UI, or packaging responsibility with no upstream equivalent, or an upstream capability gap documented in a ledger.
- **Thin adapter**: product code that only translates to an upstream entry point; upstream remains the functional authority.
- **Scheduled reduction**: code that currently carries more responsibility than its disposition allows; the reduction is already owned by an existing planned task (P3-T10+, P5, P6-T01+). No new task IDs are created by this audit.

## Memory chain (governed memory, vector store, retrieval)

| # | Capability | Evidence | Upstream entry point | License | Disposition | Owning task |
|---|---|---|---|---|---|---|
| M1 | Governed memory workflow (candidate → confirm/correct/quarantine, event log, fail-closed reads) | `forma_ai/governed_memory.py` (confirm/get/compensation flows; `get()` re-validates via `backend.get()` and raises `SEMANTICA_RECORD_MISSING`/`MISMATCH` on divergence) | Semantica `AgentContext` store/get/forget (MIT). Semantica has no candidate-approval governance workflow — capability gap accepted in ADR-004 | MIT | Justified product-owned. Semantica remains authoritative for confirmed records; product owns workflow state only | — (P6-T01/T02 re-verifies) |
| M2 | Local copy of confirmed record content | `forma_ai/governed_memory.py` `records` table write on confirm | Semantica `AgentContext.get` is the authoritative read path; the local row is a cache with fail-closed re-validation | MIT | Scheduled reduction audit item: content duplication, local history, and export semantics must be re-decided when the real Semantica binding lands | P6-T01, P6-T02 |
| M3 | Retrieval path: `retrieve()` calls product vector store directly instead of the Semantica retrieval surface | `forma_ai/adapters/semantica.py:46-54` (`embed_query` + `search_vectors` on the injected store) | Semantica v0.6.7 `AgentContext` retrieval surface (MIT) permits this injection seam, but the product bypasses the upstream retrieval entry and returns metadata-only results | MIT | Scheduled reduction: during real Semantica binding, either justify this seam as the sanctioned vector-store injection contract (and keep metadata parity) or route retrieval through the upstream entry | P6-T01, P6-T02 |
| M4 | Persistent local vector index | `forma_ai/omlx_embeddings.py` `PersistentOMLXVectorStore` (SQLite cosine-similarity index implementing the injected store protocol) | Semantica v0.6.7 ships no persistent local vector store bound to an oMLX embedding endpoint — capability gap recorded in `upstream-matrix.md` (no embedding capability proven on oMLX yet) | MIT (Semantica), Apache-2.0 (oMLX) | Justified product-owned as the injected implementation, contingent on M3's P6 decision | P6-T01 |
| M5 | oMLX embedding client (strict response validation) | `forma_ai/omlx_embeddings.py` `OMLXEmbeddingClient` | oMLX OpenAI-compatible `/v1/embeddings` endpoint (Apache-2.0) | Apache-2.0 | Thin adapter | — |
| M6 | Managed Semantica backend factory (pinned version, module-path containment, dependency injection) | `forma_ai/semantica_backend.py` (`EXPECTED_VERSION`, path containment, `AgentContext` construction) | `import semantica` under the managed runtime; upstream REST server explicitly rejected (`rejected-fixed-port-and-shallow-health-v0.6.7`) | MIT | Thin adapter | — |
| M7 | Governed memory HTTP service boundary (loopback-only, token auth, redacted audit) | `forma_ai/memory_service.py` (11 routes, `hmac.compare_digest`, body limits, semaphore) | None — Semantica's server was rejected for this role; no upstream supplies an authenticated product-internal service boundary | n/a | Justified product-owned | — |
| M8 | Embedding route approval/activation | `forma_ai/embedding_config.py` (revision approval match, vector-index model migration guard) | None upstream | n/a | Justified product-owned policy | — |
| M9 | Semantica installation inspection | `forma_ai/semantica_runtime.py` (pinned release/version/commit, restricted-env probe, module containment) | None upstream (Semantica has no managed-install inspector) | MIT | Justified product-owned lifecycle | — |
| M10 | Managed-Python memory runtime entrypoint | `scripts/semantica_memory_runtime.py` (wires GovernedMemory + real backend) | Same as M6 | MIT | Thin adapter composition | — |

## Orchestration chain (task routing, Herdr, multi-agent execution)

| # | Capability | Evidence | Upstream entry point | License | Disposition | Owning task |
|---|---|---|---|---|---|---|
| O1 | Herdr task adapter (spawn/status/cancel/resume) | `forma_ai/herdr_adapter.py` — sends `agent.start`, `agent.get`, `pane.send_keys ["ctrl+c"]` over the injected transport callable | Herdr socket CLI control surface (Apache-2.0, v0.8.2): `session.snapshot`, `events.subscribe/wait`, `agent.*`, `pane.*` per `herdr-capability-ledger.md` | Apache-2.0 | Thin adapter | — |
| O2 | Run-id ↔ task/pane correlation held only in process memory | `forma_ai/herdr_adapter.py:62-64` (`_task_ids_by_run_id`, `_pane_ids_by_run_id`, `_tasks_by_run_id` in-memory dicts) | Herdr owns runtime state; the product is allowed to persist only correlation metadata | Apache-2.0 | Scheduled reduction: correlation metadata must become durable product-owned metadata while runtime state stays in Herdr (reconnect/resume requires it) | P3-T10, P3-T13, P3-T15 |
| O3 | Herdr availability check | `forma_ai/herdr_adapter.py:66-93` (`availability()` = `which("herdr")` only, `proof="binary_discovered_only"`, status `unknown`) | Herdr `ping`/`status` over the official transport (unused today) | Apache-2.0 | Scheduled reduction: bind availability to the real transport ping; binary presence is not health | P3-T10, P3-T11 |
| O4 | Herdr event subscription, cancel semantics, reconnect/recovery | Absent — no `events.subscribe`, no reconnect logic exists yet | Herdr `events.subscribe`/`events.wait`, `session.snapshot` recovery | Apache-2.0 | Capability gap owned by plan (not drift): implementation is the pending P3 work | P3-T12, P3-T14, P3-T15 |
| O5 | Dispatch gate (Herdr execution disabled by default) | `forma_ai/supervisor.py` (`dispatch_agent_task` raises `HERDR_EXECUTION_DISABLED` unless features enabled; docstring: "Gate product task dispatch without duplicating Herdr runtime state") | n/a — policy | n/a | Justified product-owned thin gate | — |
| O6 | Task route planning (local / cloud proposal / capability unavailable) | `forma_ai/task_orchestrator.py` (deterministic planning from profiles, memory evidence, runtime phase, cloud state) | None — Herdr executes agents but has no route policy over product inference capabilities | n/a | Justified product-owned | — |
| O7 | Local task contract and completion normalization | `forma_ai/local_tasks.py` (strict schema, bounded output tokens, usage consistency checks) | None upstream | n/a | Justified product-owned contract | — |
| O8 | Supervisor CLI wiring of Herdr | `scripts/supervisor.py` `task-submit` routes only local (broker) or cloud proposal; Herdr dispatch is never invoked | Herdr control surface (pending P3) | Apache-2.0 | Consistent with P3 pending; not a duplication — no product-side multi-agent runtime is being built in its place | P3-T10+ |

## Inference chain

| # | Capability | Evidence | Upstream entry point | License | Disposition | Owning task |
|---|---|---|---|---|---|---|
| I1 | Loopback inference broker (auth, limits, audit, streaming rejection, CORS allowlist) | `forma_ai/broker.py` (`BrokerPolicy`, route allowlist, `JsonlAuditSink` redacted decisions) | oMLX OpenAI-compatible server (Apache-2.0) — upstream has no multi-client policy/audit boundary | Apache-2.0 | Justified product-owned policy boundary; adds auth/limits/audit without duplicating inference | — |
| I2 | oMLX adapter with honest health probing | `forma_ai/adapters/omlx.py` — deep probe performs a real chat completion (`"Reply with OK."`, `max_tokens 2`, ~lines 213-227) | oMLX `/v1/models`, `/v1/chat/completions`, app-bundle layout (Apache-2.0) | Apache-2.0 | Thin adapter + justified probe policy; satisfies the "health is not inference proof" drift stop | — |
| I3 | Available-memory evidence for routing | `forma_ai/system_resources.py` (`vm_stat` parse, fail-closed `AVAILABLE_MEMORY_UNKNOWN`) | None upstream | n/a | Justified product-owned | — |

## Cloud escalation chain

| # | Capability | Evidence | Upstream entry point | License | Disposition | Owning task |
|---|---|---|---|---|---|---|
| C1 | DeepSeek execution adapter | `forma_ai/deepseek_adapter.py` (redirect denial, bounded read, `_normalize` usage/cost computation at lines 133-174) | DeepSeek HTTP API (commercial terms; only approved-model execution) | Provider terms | Thin adapter | — |
| C2 | Post-execution cost ceiling verification | Gap: `_normalize` computes actual `cost_usd` but it is never compared against `approval.maximum_cost_usd`; `cloud_approval.py` `consume()` (lines 70-95) binds only the estimated ceiling | n/a — product policy obligation | n/a | Scheduled fix: verify actual cost ≤ approved ceiling after execution and surface the breach in the audit record | P5 |
| C3 | One-shot approval store | `forma_ai/cloud_approval.py` (TTL, binding to payload hash/provider/model/tokens, `fcntl` locks, 0600/0700, symlink rejection) | None upstream | n/a | Justified product-owned | — |
| C4 | Provider catalog with honest privacy fields | `forma_ai/cloud_catalog.py` (`enabled_by_default` must be False; retention "variable"; training opt-out "unknown" enforced) | None upstream | n/a | Justified product-owned | — |
| C5 | Cloud preference store (default disabled) | `forma_ai/cloud_preferences.py` | None upstream | n/a | Justified product-owned | — |
| C6 | Pending proposal/payload persistence | `forma_ai/cloud_proposals.py` (sha256+size double verification, delete after execution) | None upstream | n/a | Justified product-owned | — |
| C7 | Routing → cloud proposal creation (data-class blocks, payload hash, cost bounds, pricing staleness) | `forma_ai/inference_routing.py` | None upstream | n/a | Justified product-owned | — |

## Install / lifecycle / packaging chain

| # | Capability | Evidence | Upstream entry point | License | Disposition | Owning task |
|---|---|---|---|---|---|---|
| L1 | Pinned-artifact install transaction (journal, resume, staging, atomic activation) | `forma_ai/installer.py` (`INSTALL_STEPS`, hdiutil/ditto staging, `os.replace` activation, bundle-id gate) | oMLX ships a DMG but no product-managed lifecycle journal/activation record — capability gap | Apache-2.0 | Justified product-owned | — |
| L2 | Lifecycle operation journal | `forma_ai/lifecycle.py` (atomic snapshot + append-only events; docstring: "does not install or execute upstream software") | None upstream | n/a | Justified product-owned | — |
| L3 | Crash-safe resumable downloads with digest gates | `forma_ai/downloads.py`, `forma_ai/artifacts.py` (host allowlist, Range/206 validation, `O_NOFOLLOW`, size caps, sha256 before replace) | Generic downloaders exist but none enforce the product's pinned-sha256 + approval contract; `model_downloads.py` deliberately reuses the same gate for Hugging Face snapshots instead of `huggingface_hub` for that reason | n/a | Justified product-owned | — |
| L4 | Pinned model catalog and zero-copy external-cache links | `forma_ai/models.py` (full-file sha256 verification, config contract checks, `external-reference` symlinks with `source_ownership: external-cache-not-product-owned`) | None upstream supplies this pinning/linking contract | n/a | Justified product-owned | — |
| L5 | Read-only macOS bundle inspection | `forma_ai/macos_bundle.py` (lipo/codesign/spctl evidence) | None upstream | n/a | Justified product-owned | — |
| L6 | Fail-closed process launch contracts | `forma_ai/processes.py` (loopback-only, isolated HOME, secret-env separation) | None upstream | n/a | Justified product-owned | — |
| L7 | Supervised runtime process lifecycle with identity verification | `forma_ai/runtime.py` (pid+lstart+command-sha identity before signalling, adopt for recovery) | None upstream | n/a | Justified product-owned | — |
| L8 | Product manifest validation (component set, port policy, update gate, Semantica library-only contract) | `forma_ai/manifest.py`, `prototypes/packaging/Sources/LifecycleContract/ProductManifest.swift` | Enforces the product's own governance invariants over the four upstreams | n/a | Justified product-owned | — |
| L9 | Verified local profile catalog | `forma_ai/local_profiles.py` | None upstream | n/a | Justified product-owned | — |

## Adapter protocol and native boundary

| # | Capability | Evidence | Upstream entry point | License | Disposition | Owning task |
|---|---|---|---|---|---|---|
| A1 | Vendor-neutral adapter envelopes (identity, capability, preview, audit, health) | `forma_ai/adapter_contract.py` | Explicitly the product-owned adapter protocol per AGENTS.md; no upstream defines this product boundary | n/a | Justified product-owned | — |
| A2 | Versioned Supervisor subprocess protocol client (Swift) | `prototypes/packaging/Sources/SupervisorProtocol/SupervisorProtocol.swift` (envelope decode, request/response matching, size limits) | None upstream | n/a | Justified product-owned native boundary | — |
| A3 | Keychain runtime secrets handling | `prototypes/packaging/Sources/RuntimeSecurity/RuntimeSecrets.swift` | None upstream | n/a | Justified product-owned | — |
| A4 | Supervisor CLI command surface | `scripts/supervisor.py` (all lifecycle, runtime, task, cloud commands; frozen-aware entrypoint resolution) | Composes the layers above; no upstream duplication | n/a | Justified product-owned composition | — |

holaOS note: no holaOS code, assets, or runtime is copied into any audited path; holaOS remains an external-install reference (modified Apache-2.0, written-clearance gate), so no row carries holaOS as an upstream entry point.

## Findings that change downstream tasks (no plan-goal changes)

1. **F1 (P6-T01/T02) — retrieval seam**: `adapters/semantica.py:46-54` bypasses the Semantica retrieval surface in favor of the product-owned vector store. Decide during real Semantica binding: sanctioned injection seam (documented as such) or route through the upstream retrieval entry. Metadata-only results today.
2. **F2 (P3-T10~T15) — Herdr correlation durability and honest availability**: in-memory correlation dicts (`herdr_adapter.py:62-64`) and binary-presence-only availability (`:66-93`) must become, respectively, durable product-owned correlation metadata and a real transport ping. Runtime state stays with Herdr.
3. **F3 (P5) — actual cost vs approved ceiling**: actual `cost_usd` is computed (`deepseek_adapter.py:133-174`) but never checked against `approval.maximum_cost_usd`; the approval `consume()` path binds the estimate only (`cloud_approval.py:70-95`).
4. **F4 (P6-T01/T02) — confirmed-content duplication**: the governed-memory `records` table stores confirmed content locally (fail-closed re-validation keeps Semantica authoritative); duplication, history, and export semantics get re-decided at real binding.

## Verdict

Every audited product-owned runtime-like capability is (a) justified as a product-owned policy/orchestration/lifecycle/audit/UI/protocol responsibility with no upstream equivalent or a documented capability gap, (b) already a thin adapter over an upstream entry point, or (c) carrying a scheduled reduction that is owned by an existing planned task (P3-T10+, P5, P6-T01+). No capability requires removal outside already-planned tasks, and no audit conclusion requires changing a plan goal, requirement, or audit gate.
