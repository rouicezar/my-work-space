# Architecture Decision Log

## Accepted

- **ADR-001 — General-purpose product:** ordinary Mac users are the target; the current Mac is only an initial test environment.
- **ADR-002 — Product shell and adapters:** product-owned installer, lifecycle, policy, orchestration, and audit layers integrate replaceable upstream components.
- **ADR-003 — Progressive disclosure:** holaOS is the default UI; Herdr is optional for advanced multi-agent and terminal control.
- **ADR-004 — Governed memory authority:** Semantica owns confirmed long-term knowledge; raw input, audit, candidates, and UI session state remain distinct.
- **ADR-005 — Local-first inference:** oMLX is default; hardware profiles choose models and silent cloud fallback is prohibited.
- **ADR-006 — Safety and honest degradation:** real actions require scoped preview/approval/verification/audit; missing capability is never represented as success.
- **ADR-007 — Separate managed runtimes:** Semantica and oMLX do not share a Python environment; their dependency and upgrade constraints differ materially.
- **ADR-008 — No embedded holaOS distribution without clearance:** until written authorization resolves its modified license, public builds may integrate only with a separately installed holaOS instance and must preserve upstream branding.
- **ADR-009 — Coordinated ports and updates:** the product manifest, not upstream defaults, owns port allocation and compatibility approval. Component self-updates cannot silently bypass the tested manifest.
- **ADR-010 — Native app plus helper:** a SwiftUI `.app` is the primary product; a bundled headless helper shares its manifest and lifecycle contract. A `.pkg` is added only if a proven privileged-install requirement exists.

## Pending evidence

- **ADR-011 — Support matrix:** minimum/recommended Mac and model tiers from multi-environment measurements.
- **ADR-012 — Cloud providers:** default local-only; any provider must be separately enabled and visibly audited.
- **ADR-013 — First connector:** select a reversible connector with dedicated test accounts.
- **ADR-014 — Unified UI contingency:** obtain holaOS written clearance or validate a differently licensed product UI before claiming a single bundled application.
