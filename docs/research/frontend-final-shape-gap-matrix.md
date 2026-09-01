# Forma AI Final Frontend Shape Gap Matrix

Verified against source: 2026-09-01 Asia/Shanghai

This audit compares the current SwiftUI workbench with the bilingual target-release user guides. It is a frontend and presentation audit, not proof that any upstream runtime is installed or operational.

## Evidence inspected

- `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift`
- `prototypes/packaging/Sources/LifecycleContract/ProductManifest.swift`
- `prototypes/packaging/Sources/SupervisorProtocol/SupervisorProtocol.swift`
- both target-release user guides
- Herdr, holaOS, Semantica, and oMLX capability/reuse ledgers
- current Swift and Python tests

## Upstream-first decision record

| Required field | Decision |
|---|---|
| Upstream search result | Herdr already owns agent processes and lifecycle; holaOS exposes workflow/application/tool candidates; Semantica owns confirmed knowledge; oMLX owns model inference. None owns the independent Forma AI native SwiftUI presentation. |
| Reusable entry points | Herdr snapshot/events/agent/pane APIs; holaOS runtime/harness/tool surfaces pending pinned validation; Semantica AgentContext adapter; oMLX health/models/chat/embedding APIs. |
| License obligation | Preserve Herdr Apache-2.0 notices; do not copy or rebadge holaOS frontend/assets; recheck exact Semantica/oMLX distribution obligations at release. |
| Integration decision | Build only native presentation contracts and preview fixtures. Runtime mode must consume thin adapters over upstream authority. |

## Primary navigation decision

The current three-destination navigation is retained:

1. `New task`
2. `History`
3. `Settings`

Approvals remain contextual inside a task and configurable under Permissions & Approvals. Memory review and Agents & Tools remain full Settings surfaces. This matches the target guide and avoids turning ordinary use into an administration dashboard.

## Screen gap matrix

| Surface | Target-release experience | Current SwiftUI evidence | Gap | Upstream authority | Preview boundary |
|---|---|---|---|---|---|
| New task empty state | Clear goal entry, privacy/route summary, useful starter actions | Present: prompt, route picker, privacy copy | Needs task templates, attachment/context affordance, and clearer route explanation | Forma UI; oMLX/cloud route facts | Synthetic examples only; no task submission in preview |
| Task execution thread | Goal → plan/route → agents → approvals → artifacts → validation → result | Local/cloud result states exist; no unified execution thread | Major redesign required | Herdr states, oMLX/cloud result, Forma policy/audit | Deterministic scenario timeline |
| Parallel agents | Owner, role, state, blocker, elapsed time, artifacts, logs, cancel/resume | Two-card DEBUG fixture only | Missing real state range, hierarchy, actions, output detail | Herdr | Preview cards visibly labeled and inert |
| Approval request | Exact action/data/cost/effect, approve/deny, expiry | Cloud proposal present | Generalize to external writes, delete, execute, force stop; add before/after and reversibility | Forma policy; connector/upstream operation facts | Buttons change preview scenario only, never runtime |
| Artifacts and validation | Produced files, owner, digest/type, validation, open/review actions | No unified artifact surface | Entire surface missing | Herdr artifact metadata plus product validation | Synthetic bounded metadata; no filesystem path opening |
| Final result | Completion category, evidence, unresolved items, audit | Local/cloud result cards present | Add partial/cancelled/interrupted and validation summary | Upstream result plus Forma audit | Read-only scenario result |
| History list | Persistent tasks with search/filter/status/updated time | Empty-state contract only | Entire list/detail design missing | Product metadata projection; Herdr truth | Synthetic history store in memory only |
| History detail | Task identity, execution timeline, agents, approvals, artifacts, audit | Missing | Entire surface missing | Herdr + product correlation | Read-only scenario detail |
| Recovery | Explain interruption, exact recoverability, resume/fresh-run/cancel | Contract only; no controls | Entire surface missing | Herdr snapshot/session/revision | Inert controls or local scenario transition only |
| General settings | Language, appearance, launch, update channel | Informational notice | Controls missing | Forma lifecycle/UI | Preview preferences not persisted |
| Models & Providers | Local profiles, provider credential state, test/remove, routing policy | Cloud credential and model setup partly present | Consolidate hierarchy; preview final success/error/disabled states | oMLX and provider APIs; Keychain | No Keychain access in preview |
| Agents & Tools | Installed adapters, capability, health, scopes, versions, disable/remove | Informational notice | Entire management surface missing | Herdr and holaOS manifests/APIs | Synthetic capabilities; no process/plugin action |
| Memory | Status, candidates, confirmed items, conflicts, corrections, export/delete | Embedding setup plus notice | Review and governance surfaces missing | Semantica | Synthetic records; no persistence |
| Permissions & Approvals | Policy by action/scope, pending approvals, standing grants, revoke | Informational notice | Entire policy-management surface missing | Forma policy; upstream capability declarations | Read-only policy fixture; no grant creation |
| Local Runtime | Install/start/stop/sample/status | Substantial controls present | Needs final hierarchy, resource/profile summary, multi-component state | oMLX plus product lifecycle | No process actions in preview |
| Data & Privacy | Routes, storage, retention, credentials, audit export/redaction | Informational notice | Entire management surface missing | Forma lifecycle/policy; Semantica data facts | Synthetic storage summary; no file/export operation |
| Diagnostics & Recovery | Component/workflow health, logs, repair, rollback, diagnostic export | Installation/preflight controls partly present | Needs component graph, workflow health, repair plan, redaction review | All upstream health plus Forma lifecycle | No repair/process/file action in preview |
| First-run setup | Separate guided compatibility/model/memory/permission/sample flow | Setup controls distributed in Settings | Dedicated guided flow missing | Forma lifecycle using upstream installers/APIs | Preview walkthrough only |

## State coverage matrix

Every final frontend must distinguish these states without relying on color alone:

| Domain | Required states |
|---|---|
| Task | draft, planning, running, awaiting approval, blocked, partial, succeeded, failed, cancelled, interrupted, unknown |
| Agent | queued, starting, running, blocked, succeeded, failed, cancelled, interrupted, unknown |
| Approval | not required, pending, approved once, denied, expired, consumed, invalidated |
| Artifact | declared, available, validating, valid, invalid, missing, external-unverified |
| Component | not installed, stopped, starting, ready, degraded, incompatible, unavailable, unknown |
| Memory | candidate, confirmed, conflict, corrected, rejected, deleted, unavailable |
| Route | local, cloud proposal required, approved cloud, capability unavailable |

Current SwiftUI covers only a subset. P4-T11 must encode the full presentation set without creating runtime semantics.

## Final-shape priority

1. Task execution thread and parallel Agent area.
2. History detail and recovery.
3. Memory review.
4. Agents & Tools plus Permissions & Approvals.
5. Consolidated Models/Runtime/Privacy/Diagnostics.
6. First-run guided setup.

This order gives the user the recognizable product core first. It does not change upstream integration ownership or allow later runtime work to be skipped.

## P4-T10 exit boundary

P4-T10 is complete when this matrix and the Product Preview presentation contract agree on navigation, state vocabulary, upstream authority, and preview isolation. No UI implementation or runtime claim belongs to this task.
