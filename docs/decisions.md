# Architecture Decision Log

## Accepted

- **ADR-001 — General-purpose product:** ordinary Mac users are the target; the current Mac is only an initial test environment.
- **ADR-002 — Product shell and adapters:** product-owned installer, lifecycle, policy, orchestration, and audit layers integrate replaceable upstream components.
- **ADR-003 — Superseded interaction split:** the earlier holaOS-default/Herdr-optional split is superseded by ADR-017 and the 2026-08-31 master plan. The product-owned workbench is the default UI; holaOS contributes reusable non-visual capabilities through the licensed integration boundary; Herdr is the core multi-agent runtime.
- **ADR-004 — Governed memory authority:** Semantica owns confirmed long-term knowledge; raw input, audit, candidates, and UI session state remain distinct.
- **ADR-005 — Local-first inference:** oMLX is default; hardware profiles choose models and silent cloud fallback is prohibited.
- **ADR-006 — Safety and honest degradation:** real actions require scoped preview/approval/verification/audit; missing capability is never represented as success.
- **ADR-007 — Separate managed runtimes:** Semantica and oMLX do not share a Python environment; their dependency and upgrade constraints differ materially.
- **ADR-008 — No embedded holaOS distribution without clearance:** until written authorization resolves its modified license, public builds may integrate only with a separately installed holaOS instance and must preserve upstream branding.
- **ADR-009 — Coordinated ports and updates:** the product manifest, not upstream defaults, owns port allocation and compatibility approval. Component self-updates cannot silently bypass the tested manifest.
- **ADR-010 — Native app plus helper:** a SwiftUI `.app` is the primary product; a bundled headless helper shares its manifest and lifecycle contract. A `.pkg` is added only if a proven privileged-install requirement exists.
- **ADR-012 — Explicit dual-model routing:** local Qwen through oMLX is the default;
  DeepSeek is optional and disabled by default. Every cloud transmission requires an
  exact, one-shot, audited approval and provider/model/price data remain replaceable
  catalog entries.
- **ADR-015 — Private local task protocol:** daily user text reaches the authenticated
  local broker through Supervisor standard input, with bounded output, redacted audit,
  and no silent cloud fallback.
- **ADR-016 — Unified task routing state:** product-owned local capability profiles,
  runtime health, private cloud preferences, and current provider catalogs determine
  routing; UI state and model self-assessment are not authoritative.
- **ADR-017 — Independent workbench with upstream-first reuse:** implement the product-owned workbench and adapter protocol, while reusing licensed non-visual functionality from Semantica, holaOS, Herdr, and oMLX before creating new equivalents. Herdr is required for the core multi-agent loop. Public distribution is gated separately from personal non-commercial development.

### P1 upstream reuse decisions

- **Reuse decision — Semantica (`v0.6.7`, commit `ecb33a5b7d1c232da77527da89d861e2b10e9c42`):** reuse `AgentContext` and upstream memory, decision, causal, provenance, graph, export, and MCP surfaces inside a separately managed runtime. Semantica is the only governed long-term knowledge and decision-evidence authority. Forma AI owns candidate/confirmation policy, user approval, isolation, correlation, redacted audit, adapter lifecycle, and native review UI. Building a second durable memory or decision engine is forbidden unless the pinned upstream lacks a required capability and the gap is recorded. Acceptance requires real write/read/retrieve/forget and decision/provenance contract tests through the managed adapter; route health alone is insufficient. MIT notice and dependency licenses must ship where applicable. Evidence: `docs/research/upstream-matrix.md`.

- **Reuse decision — holaOS (reviewed commit `4684714ee133794cdbb86630e42b7d93447fb2e2`):** during private personal development, evaluate and reuse eligible non-visual runtime, harness, state-store, client, app-host, and SDK implementation behind a versioned adapter before creating equivalents. Use MCP, skills, providers, integrations, browser, automation, and artifact workflows as parity requirements until their exact source entry points are mapped. Forma AI owns the independent macOS workbench, branding, navigation, policy, approval, and governed memory boundary; holaOS durable memory may not compete with Semantica. Do not copy or bundle the shared UI, desktop frontend, logos, or branded assets. Public embedding remains blocked without exact-path review and written clearance; a separately installed, version-fingerprinted adapter is the preferred fallback but is not assumed to bypass the license. Acceptance requires pinned-source acquisition plus adapter/security tests, not README claims. Evidence: `docs/research/holaos-capability-ledger.md` and `docs/research/license-matrix.md`.

- **Reuse decision — Herdr (`v0.8.2`, commit `9eb521456ac0d19d3ab3d9d7cea3cca10baa8a4c`):** use the digest-verified official binary as the mandatory multi-agent execution runtime, with CLI wrappers for simple operations and the local socket API for schema/version checks, snapshots, subscriptions, dispatch, semantic state, prompt/wait, output, worktrees, detach/reconnect, and supported native resume. Forma AI owns task intent/graph, approvals, user-visible ownership, audit correlation, reconnect reconciliation, and its native UI; it must not implement a competing cosmetic executor. Cancellation is an explicit product policy over safe pane/process controls because the reviewed API has no single `agent.cancel`. Acceptance requires two real parallel fixture agents plus state, block, cancel, reconnect, resume, and recovery tests. Apache notices, binary digest, vendored code, integration assets, and trademarks remain release gates. Evidence: `docs/research/herdr-capability-ledger.md`.

- **Reuse decision — oMLX (`v0.6.3`, commit `85708e4b9a585df42241c826b6be2b4dba018406`):** use the verified official macOS artifact as the default local inference runtime behind the product-owned authenticated loopback broker. Reuse its OpenAI-compatible generation, embedding, rerank, Messages, Responses, model, and optional tool surfaces only when each route/model capability is explicitly selected and tested; do not rebuild its inference engine or casually recreate its ABI-coupled Python environment. Forma AI owns Keychain credentials, port allocation, isolation, admission/rate/size limits, model catalog/ownership, routing, audit, update coordination, and user approvals. `/health`, `/v1/models`, and route existence never prove inference or model capability. Chat is verified only for the exact pinned Qwen pair; embedding and the remaining real-runtime gates stay pending. Apache notices, dependencies, native kernels, models, updater, signing, and notarization remain distribution gates. Evidence: `docs/research/upstream-matrix.md` and `docs/runbooks/omlx.md`.

## Pending evidence

- **ADR-011 — Support matrix:** minimum/recommended Mac and model tiers from multi-environment measurements.
- **ADR-013 — First connector:** select a reversible connector with dedicated test accounts.
- **ADR-014 — Unified UI contingency:** obtain holaOS written clearance or validate a differently licensed product UI before claiming a single bundled application.
