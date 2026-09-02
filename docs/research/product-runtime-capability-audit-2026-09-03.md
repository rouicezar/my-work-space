# Product-Owned Runtime Capability Audit — Stage Review

Date: 2026-09-03
Executor: Claude agent
Predecessor: `product-runtime-capability-audit-2026-09-01.md` (P1-T09)

Scope: a stage review of completed work (P0 through P4-T14), re-auditing the work done after the 2026-09-01 audit — P3-T10 through P3-T17 (real Herdr runtime) and P4-T10 through P4-T14 (frontend-shape-first Preview surfaces) — for two properties: (1) goal alignment and (2) upstream duplication.

## Method

- Document-level goal alignment against `docs/product-requirements.md` (FR-1 through FR-11), the four upstream reuse decisions in `docs/decisions.md`, and the milestone tracker.
- Code-level review across four subsystems (Herdr execution runtime; Herdr lifecycle/process; memory/inference/cloud/orchestration; Swift frontend Preview), run as four parallel read-only reviews, each audited against the four capability ledgers and the 2026-09-01 audit matrix.

## Goal alignment — no drift

| Check | Verdict | Evidence |
|---|---|---|
| Not degraded into setup wizard / model downloader / single-chat demo / thin wrapper | Pass | P3 proves real multi-agent execution (4 live Herdr integration tests), not cosmetic UI |
| Herdr is the required core multi-agent runtime, not optional | Pass | P3 milestone verified |
| Semantica is the sole governed long-term memory authority | Pass | `governed_memory.py` confirms into Semantica first, then caches; `get()` re-validates via `backend.get()` |
| holaOS frontend/assets/trademarks not copied or bundled | Pass | holaOS ledger marks shared UI / desktop as exclude; external-install reference only |
| Local-first inference with per-request cloud approval | Pass | ADR-005/012; DeepSeek off by default |
| Preview cannot become runtime acceptance evidence | Pass | Synthetic data carries explicit "preview" markers; `runtimeActionsAllowed=false` across all surface contracts |

## Upstream duplication — none new

| Subsystem | Verdict | Key determination |
|---|---|---|
| Herdr execution runtime (`herdr_transport.py`, `herdr_adapter.py`, `herdr_presentation.py`) | Thin adapter / projection | The four in-memory dicts are claim/correlation caches, not state authority; every state read re-reads `agent.get`/`session.snapshot` |
| Herdr lifecycle/process (`processes.py`, `runtime.py`, `scripts/supervisor.py`) | Process lifecycle only | The "herdr" runtime role only does start/stop/status, treated identically to omlx/broker/memory; `herdr-snapshot` is a fail-closed pass-through of `session.snapshot` |
| Memory/inference/cloud/orchestration (`governed_memory.py`, `memory_service.py`, `adapters/semantica.py`, `semantica_backend.py`, `omlx_embeddings.py`, `broker.py`, `adapters/omlx.py`, `deepseek_adapter.py`, `task_orchestrator.py`, `supervisor.py`) | Governance staging + thin adapters | The `records` table is a fail-closed content cache, not a second authority; the vector index fills a recorded upstream gap (Semantica v0.6.7 ships no oMLX-bound persistent vector store) |
| Swift frontend Preview (`ProductPreviewProvider.swift`, `GovernedMemoryReviewPreview.swift`, `HistoryRecoveryPreview.swift`, `ExecutionJourneyPreview.swift`, `DailyWorkbenchPreview.swift`, `FormaAIApp.swift`, `SupervisorProtocol.swift`) | Read-only presentation contract | No runtime/Keychain/network/write path; runtime mode binds the real Herdr snapshot and honestly shows "Disconnected" on failure |

## Findings tracking

| Finding | Status |
|---|---|
| F1 retrieval seam (bypasses Semantica retrieval) | Open — owned by P6-T01/T02 |
| F2 Herdr correlation durability + honest availability | Resolved — P3-T11 transport ping, P3-T15 reclaim |
| F3 actual cost vs approved ceiling | Open — owned by P5 |
| F4 confirmed-content local duplication | Open — owned by P6-T01/T02 |
| F5 obsolete `spawn_reported_task()` | Resolved — removed in the P1-T09 correction |

## Residual (non-blocking)

- F1/F3/F4 remain correctly owned by P5/P6; this audit confirms they are still in their intended unresolved state with no premature drift.
- `ProductPreviewWorkspace.swift` and `FirstRunPreview.swift` were outside the four review file lists; a follow-up read-only review is recommended, though their contract fields already declare the read-only boundary.

## Verdict

Completed work (P0 through P4-T14) does not drift from the product goal and does not reimplement upstream non-visual capabilities. Every finding maps to the already-tracked F1–F5 set; no new drift or duplication was introduced.
