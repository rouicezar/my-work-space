# Architecture Decision Log

## Accepted

### ADR-001 — Isolated first deployment

Phase one is independent from MyNote, GBrain, existing automations, persistent agent rules, and production accounts. Migration is a separate future project after manual acceptance.

### ADR-002 — Dual control planes, one knowledge authority

holaOS is the default daily entry point. Herdr is the advanced development and multi-agent console. They coordinate through stable interfaces and project artifacts; neither owns the other's runtime.

### ADR-003 — Semantica is authoritative only for governed long-term knowledge

Raw input, transient chat state, and unverified summaries are not authoritative memory. Confirmed knowledge requires provenance, classification, and validation.

### ADR-004 — oMLX is the default local inference service

Clients use compatibility APIs rather than project-specific source coupling. Actual models and capability thresholds are selected after live hardware and tool-call benchmarks.

## Pending

### ADR-005 — Cloud fallback policy

Choose whether phase-one acceptance is strictly local-only or allows a manually approved cloud escalation path. Until confirmed, cloud escalation is disabled by default.

### ADR-006 — Exact Mac hardware envelope

Record chip, RAM, free disk, macOS version, and acceptable sustained load before selecting models.
