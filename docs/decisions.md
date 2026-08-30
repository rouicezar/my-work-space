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

## Pending evidence

- **ADR-011 — Support matrix:** minimum/recommended Mac and model tiers from multi-environment measurements.
- **ADR-013 — First connector:** select a reversible connector with dedicated test accounts.
- **ADR-014 — Unified UI contingency:** obtain holaOS written clearance or validate a differently licensed product UI before claiming a single bundled application.
