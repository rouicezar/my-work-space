# Architecture Decision Log

## Accepted

- **ADR-001 — General-purpose product:** ordinary Mac users are the target; the current Mac is only an initial test environment.
- **ADR-002 — Product shell and adapters:** product-owned installer, lifecycle, policy, orchestration, and audit layers integrate replaceable upstream components.
- **ADR-003 — Progressive disclosure:** holaOS is the default UI; Herdr is optional for advanced multi-agent and terminal control.
- **ADR-004 — Governed memory authority:** Semantica owns confirmed long-term knowledge; raw input, audit, candidates, and UI session state remain distinct.
- **ADR-005 — Local-first inference:** oMLX is default; hardware profiles choose models and silent cloud fallback is prohibited.
- **ADR-006 — Safety and honest degradation:** real actions require scoped preview/approval/verification/audit; missing capability is never represented as success.

## Pending evidence

- **ADR-007 — Packaging:** native managed-services app versus signed package/launcher.
- **ADR-008 — Licensing:** determine bundling versus first-run download for each upstream component.
- **ADR-009 — Support matrix:** minimum/recommended Mac and model tiers from multi-environment measurements.
- **ADR-010 — Cloud providers:** default local-only; any provider must be separately enabled and visibly audited.
- **ADR-011 — First connector:** select a reversible connector with dedicated test accounts.
