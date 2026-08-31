# Multi-Agent Workbench Master Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build Forma AI, a local-first Mac AI workbench where a small local model can coordinate parallel agents, reuse Semantica, holaOS, Herdr, and oMLX through adapters, and combine local and approved cloud models for real work.

**Architecture:** The product-owned native workbench is the default distributable UI. Licensed non-visual holaOS workflow/application capabilities are reused behind the adapter boundary, while its visual assets and public bundling remain separately gated. Herdr is the core multi-agent execution runtime, Semantica is the governed memory authority, and oMLX is the local inference runtime.

**Tech Stack:** SwiftUI macOS app, Python supervisor/adapters, Herdr socket/CLI integration, oMLX OpenAI-compatible API, Semantica REST/MCP, Keychain-held cloud credentials, repository-local tests and fixtures.

**Build rule:** Reuse licensed non-visual capabilities from Semantica, holaOS, Herdr, and oMLX before implementing product-owned equivalents. Product-owned development is reserved for the independent visual workbench, adapter protocol, integration/orchestration/policy/lifecycle, license-blocked portions, or evidenced upstream gaps.

---

## Control Rules

This is the authoritative execution and progress tracker for the Forma AI project.

- Every agent must read this full file, `docs/TASK_HANDOFF.md`, and `AGENTS.md` before changing product code.
- Every task must have exactly one status: `pending`, `in_progress`, `blocked`, `verified`, or `dropped`.
- Only one task may be `in_progress` at a time unless the user explicitly starts parallel agent work.
- A task is not complete until this tracker and `docs/TASK_HANDOFF.md` are both updated.
- Progress is evidence-based. Do not mark `verified` from visual inspection, intent, or a passing health endpoint alone.
- Any change to product goal, upstream reuse policy, memory authority, or cloud credential behavior requires explicit user approval.
- If another agent takes over, it must claim a task ID here and write a handoff entry before and after its work.
- On Codex quota warning, stop opening new work, close and verify the smallest safe unit, update both control documents, commit and push verified work, and leave a clean repository. Preserve and explicitly inventory any pre-existing dirty work that cannot safely be removed.

## Current State

Updated: 2026-08-31 Asia/Shanghai
Current phase: P2 Adapter protocol and contracts
Current task: P2-T08
Current status: pending
Next action: audit the complete P2 contract chain, run the protocol tests, commit any final closeout record, and verify the phase exit gate.

Known uncommitted implementation work that must not be overwritten by this documentation task:

- `forma_ai/deepseek_adapter.py`
- `tests/test_deepseek_adapter.py`
- `prototypes/packaging/Sources/LifecycleContract/ProductManifest.swift`
- `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift`
- `prototypes/packaging/Tests/LifecycleContractTests/ProductManifestTests.swift`
- `build/`
- `evidence/ui/cloud-settings-review-2026-08-31.png`

Known evidence from the interrupted task:

- DeepSeek adapter tests had been adjusted around urllib timeout handling and unexpected error classification.
- DeepSeek real provider reached once but returned `DEEPSEEK_RESPONSE_INVALID`; the observed hypothesis was that thinking mode consumed the small output budget. This is not yet a verified closed loop.
- Swift package tests for packaging previously reported 30 passed and 2 skipped.
- Python targeted DeepSeek/Supervisor tests previously reported 43 passed.
- The UI screenshot evidence is not sufficient because the captured image did not prove the foreground app state.

## Product Non-Negotiables

1. The product is a local-first multi-agent AI workbench, not a setup wizard.
2. The first screen must support actual task creation, conversation, history, recovery, model selection, and supervised agent execution.
3. The workbench must coordinate multiple agents in parallel with readable state, ownership, cancellation, and recovery.
4. Local small models must be usable for routing, summarization, memory lookup, and low-risk control decisions.
5. Cloud models, including DeepSeek, are allowed only through explicit credential setup, policy preview, user approval, and audit logs.
6. Semantica is the governed long-term memory authority.
7. Herdr is the core multi-agent execution engine, not an optional afterthought.
8. oMLX is the local inference layer and must prove real inference, not only health.
9. holaOS capability parity is required, but public distribution must avoid copying or rebadging holaOS frontend/source/assets until license clearance.
10. Future public open-source distribution must preserve license notices, secrets boundaries, and a clean adapter-based reuse story.
11. A local model must be able to discover and coordinate Codex, Claude, and other compatible AI tools through a vendor-neutral agent adapter contract.
12. Settings must be a complete product surface: General, Models & Providers, Agents & Tools, Memory, Permissions & Approvals, Local Runtime, Data & Privacy, and Diagnostics & Recovery.
13. No non-visual upstream capability may be reimplemented without a recorded upstream search and a license, compatibility, security, maintainability, or verified capability-gap reason.

## Upstream Reuse Ledger

| Upstream | Role | Reuse mode | Must not do | Verification gate |
|---|---|---|---|---|
| Semantica | Governed memory, decisions, provenance | Reuse via REST/MCP/package where licensed | Create a competing long-term memory authority | Memory write/read contract test plus audit event |
| holaOS | Workflow/application capability source plus optional external interface | Reuse licensed non-visual code/APIs in personal development; retain adapter boundary for distribution | Copy, rebadge, or bundle restricted frontend assets in public release | Capability/reuse ledger, notices, and adapter smoke test |
| Herdr | Core multi-agent execution runtime | Pin and integrate CLI/socket/API | Treat multi-agent as cosmetic UI only | Parallel task execution, cancel, resume, reconnect tests |
| oMLX | Local inference runtime | Verified runtime or official artifact acquisition | Treat `/health` as inference proof | Chat completion or embedding inference proof with model ID |

## Capability Parity Ledger

Status values: `not_started`, `mapped`, `implemented`, `verified`.

| ID | Capability | Reference source | Product target | Status | Evidence |
|---|---|---|---|---|---|
| CAP-01 | New task conversation | Codex/holaOS-style workbench | First screen starts a real task with local/cloud routing | not_started | None |
| CAP-02 | Multi-agent parallel work | Herdr/holaOS/Codex | Multiple visible workers with owner, state, logs, and artifacts | not_started | None |
| CAP-03 | Agent command and review loop | Codex-style task execution | User can assign, inspect, interrupt, resume, and review | not_started | None |
| CAP-04 | Local model control | oMLX | Local model can route/summarize/answer simple requests | partial | oMLX setup exists; runtime stopped in screenshot |
| CAP-05 | Cloud model setup | DeepSeek/OpenAI-compatible providers | Settings has provider list, credential state, low-cost test, and removal | partial | Uncommitted DeepSeek/settings work exists |
| CAP-06 | Governed memory | Semantica | Retrieval, candidate memory, approval, audit | not_started | None |
| CAP-07 | History and recovery | Product workbench | Task history, failed run recovery, cancel/resume | partial | Sidebar exists; user reports unclear product function |
| CAP-08 | Tool/process console | Herdr | Task execution logs and external tool lifecycle | not_started | None |
| CAP-09 | Permission and audit | Product policy layer | External writes and cloud calls require preview/approval/audit | partial | Policy intent exists; full UI not verified |
| CAP-10 | Distribution readiness | Packaging/lifecycle | Clean install, upgrade, rollback, uninstall, recovery gates | partial | Packaging tests exist; product experience incomplete |
| CAP-11 | Universal agent adapters | Codex/Claude/compatible tools | Capability discovery, dispatch, status, handoff, cancel, resume, artifacts, audit | not_started | None |
| CAP-12 | Complete product settings | Product workbench | General, providers, agents/tools, memory, permissions, runtime, privacy, diagnostics/recovery | not_started | Current screen is setup/recovery only |

## Milestone Tracker

| Phase | Goal | Status | Exit Gate |
|---|---|---|---|
| P0 | Correct governance and stop product drift | verified | Tracker, handoff, role documents, and upstream-first reuse rules agree |
| P1 | Inventory upstream capabilities and licenses | verified | Reuse decisions for all four upstreams have evidence |
| P2 | Define adapter protocol and contracts | pending | Protocol tests cover Semantica, holaOS, Herdr, oMLX, cloud providers |
| P3 | Make Herdr-backed multi-agent loop real | pending | Two parallel tasks run, stream status, cancel, resume, and recover |
| P4 | Make independent workbench usable | pending | First-run user can start a task without visiting recovery settings |
| P5 | Make local/cloud model cooperation real | pending | oMLX local proof plus approved low-cost DeepSeek loop |
| P6 | Make Semantica governed memory real | pending | Retrieval, candidate memory, approval, and audit verified |
| P7 | Finish history, cancellation, and recovery | pending | Interrupted task can resume from persisted state |
| P8 | Distribution and public-source hardening | pending | License/SBOM/secrets/clean-install gates pass |

## Granular Task List

### P0: Governance Correction

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P0-T01 | verified | Create this master plan and tracker | `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md` | `test -f docs/plans/2026-08-31-multi-agent-workbench-master-plan.md` | File exists |
| P0-T02 | verified | Create the takeover handoff document | `docs/TASK_HANDOFF.md` | `test -f docs/TASK_HANDOFF.md` | File exists |
| P0-T03 | verified | Update startup and completion rules | `AGENTS.md` | `rg -n "Execution control documents|Task Handoff" AGENTS.md` | Required rules found |
| P0-T04 | verified | Verify documentation-only diff | This file, `docs/TASK_HANDOFF.md`, `AGENTS.md` | `git diff --check -- AGENTS.md docs/plans/2026-08-31-multi-agent-workbench-master-plan.md docs/TASK_HANDOFF.md` | No whitespace errors |
| P0-T05 | verified | Commit governance docs only | Same files | `git add AGENTS.md docs/plans/2026-08-31-multi-agent-workbench-master-plan.md docs/TASK_HANDOFF.md` then `git commit -m "docs: add workbench execution control"` | Commit `3756677` created without staging implementation work |
| P0-T06 | verified | Push governance docs | Same files | `git push` | Governance documentation commits are ready to push with this completion update |
| P0-T07 | verified | Reconcile product-role conflicts and enforce upstream-first reuse | `AGENTS.md`, requirements, decisions, ADRs, active/legacy plans, handoff | `rg` conflict scan plus `git diff --check` | Conflicting role statements are superseded or corrected; upstream-first rule, universal agent adapter, and full Settings scope are explicit |
| P0-T08 | verified | Rename product globally to Forma AI and add an original macOS icon | tracked source, tests, docs, packaging, app assets, filenames | legacy-name absence scan, Python tests, Swift tests, app bundle inspection | Tracked product surface has no legacy name; 225 Python tests passed with 1 skipped; 30 Swift tests passed with 2 skipped; signed Forma AI app contains valid ICNS |

### P1: Upstream Capability and License Inventory

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P1-T01 | verified | List available local upstream checkouts and pins | `docs/research/upstream-matrix.md` | `rg --files . | rg "(hola|herdr|semantica|omlx)"` | Local sources, installed oMLX artifact, declared pins, search boundaries, and gaps documented |
| P1-T02 | verified | Refresh Semantica API/capability evidence | `docs/research/upstream-matrix.md` | `rg -n "semantica|mcp|server|memory" .` | Commit, release digests, entry points, dependencies, capability reuse map, and product boundary documented from official v0.6.7 sources |
| P1-T03 | verified | Refresh holaOS capability and reusable-implementation map | `docs/research/holaos-capability-ledger.md` | `test -f docs/research/holaos-capability-ledger.md` | Capability map distinguishes reusable code, required notices, visual assets, and distribution restrictions |
| P1-T04 | verified | Refresh Herdr socket/CLI capability map | `docs/research/herdr-capability-ledger.md` | `test -f docs/research/herdr-capability-ledger.md` | Multi-agent capabilities mapped |
| P1-T05 | verified | Refresh oMLX API and model capability evidence | `docs/research/upstream-matrix.md` | `rg -n "omlx|OpenAI-compatible|/v1" docs/research/upstream-matrix.md` | Runtime assumptions updated |
| P1-T06 | verified | Reconcile license matrix with public open-source intent | `docs/research/license-matrix.md` | `rg -n "public|redistribution|holaOS" docs/research/license-matrix.md` | Public distribution constraints explicit |
| P1-T07 | verified | Add a reuse decision record for each upstream | `docs/decisions.md` | `rg -n "Reuse decision" docs/decisions.md` | Four decisions recorded |
| P1-T08 | verified | Commit upstream inventory docs | Research docs, `docs/decisions.md` | `git diff --check` then `git commit` | Commit includes only inventory docs |

### P2: Adapter Protocol Contract

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P2-T01 | verified | Write failing test for adapter identity and health envelope | `tests/test_adapter_contract.py` | `python -m unittest tests.test_adapter_contract -v` | Fails because contract is absent |
| P2-T02 | verified | Add minimal protocol dataclasses | `forma_ai/adapter_contract.py` | `python -m unittest tests.test_adapter_contract -v` | Identity/health tests pass |
| P2-T03 | verified | Write failing test for capability declaration | `tests/test_adapter_contract.py` | `python -m unittest tests.test_adapter_contract -v` | Fails on missing capabilities |
| P2-T04 | verified | Implement capability declaration model | `forma_ai/adapter_contract.py` | `python -m unittest tests.test_adapter_contract -v` | Capabilities pass |
| P2-T05 | verified | Write failing test for policy preview/audit fields | `tests/test_adapter_contract.py` | `python -m unittest tests.test_adapter_contract -v` | Fails on missing policy fields |
| P2-T06 | verified | Implement policy preview/audit envelope | `forma_ai/adapter_contract.py` | `python -m unittest tests.test_adapter_contract -v` | Contract tests pass |
| P2-T07 | verified | Specify vendor-neutral AI agent adapter for Codex, Claude, and compatible tools | `docs/contracts/agent-adapter.md`, contract tests | `python3 -m unittest tests.test_agent_adapter_contract tests.test_adapter_contract -v` | Discovery, dispatch, status, handoff, cancel, resume, artifacts, and audit are covered |
| P2-T08 | pending | Commit adapter contract | Adapter contract, agent contract, and tests | `git diff --check` then `git commit` | Commit created |

### P3: Herdr Core Multi-Agent Runtime

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P3-T01 | pending | Write failing Herdr adapter availability test | `tests/test_herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Fails before adapter exists |
| P3-T02 | pending | Add Herdr adapter skeleton using adapter contract | `forma_ai/herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Availability test passes |
| P3-T03 | pending | Write failing test for spawning two mock tasks | `tests/test_herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Fails on missing spawn |
| P3-T04 | pending | Implement mockable task spawn/status methods | `forma_ai/herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Two tasks have stable IDs and states |
| P3-T05 | pending | Write failing test for cancel and resume envelope | `tests/test_herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Fails on missing lifecycle |
| P3-T06 | pending | Implement cancel/resume mapping | `forma_ai/herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Lifecycle tests pass |
| P3-T07 | pending | Wire supervisor to Herdr adapter behind feature flag | `forma_ai/supervisor.py` | `python -m unittest discover tests -v` | Existing tests pass |
| P3-T08 | pending | Add UI task state fixture for parallel agents | `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift` | `swift test --package-path prototypes/packaging` | Swift tests pass |
| P3-T09 | pending | Commit Herdr core slice | Adapter, supervisor, tests, Swift fixture | `git diff --check` then `git commit` | Commit created |

### P4: Independent Workbench Product Experience

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P4-T01 | pending | Write UI contract test for first-screen task composer | `prototypes/packaging/Tests/LifecycleContractTests/ProductManifestTests.swift` | `swift test --package-path prototypes/packaging` | Fails before composer contract |
| P4-T02 | pending | Move daily work surface above setup/recovery | `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift` | `swift test --package-path prototypes/packaging` | Contract passes |
| P4-T03 | pending | Add model/provider selection contract | Lifecycle contract tests | `swift test --package-path prototypes/packaging` | Provider selector required |
| P4-T04 | pending | Implement cloud/local model selector state | Swift app and manifest files | `swift test --package-path prototypes/packaging` | Selector state passes tests |
| P4-T05 | pending | Add task history visible state contract | Swift tests | `swift test --package-path prototypes/packaging` | History state test passes |
| P4-T06 | pending | Add recovery action visible state contract | Swift tests | `swift test --package-path prototypes/packaging` | Recovery state test passes |
| P4-T07 | pending | Add complete Settings information architecture and contracts | Swift app, manifest, and tests | `swift test --package-path prototypes/packaging` | All eight settings sections are reachable and setup/recovery is separated |
| P4-T08 | pending | Capture foreground UI evidence | `evidence/ui/workbench-first-screen-YYYY-MM-DD.png` | Manual launch plus screenshot review | Screenshot proves first screen is workbench |
| P4-T09 | pending | Commit workbench product experience slice | Swift files, tests, evidence if allowed | `git diff --check` then `git commit` | Commit created |

### P5: Local and Cloud Model Cooperation

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P5-T01 | pending | Reproduce current DeepSeek failure with test credential only | `evidence/cloud/deepseek-YYYY-MM-DD.md` | Approved low-cost test command | Error or success captured without secret |
| P5-T02 | pending | Add failing test for DeepSeek output budget handling | `tests/test_deepseek_adapter.py` | `python -m unittest tests.test_deepseek_adapter -v` | Fails on invalid small response path |
| P5-T03 | pending | Fix DeepSeek low-cost chat completion path | `forma_ai/deepseek_adapter.py` | `python -m unittest tests.test_deepseek_adapter -v` | Tests pass |
| P5-T04 | pending | Run one approved real DeepSeek closed loop | `evidence/cloud/deepseek-YYYY-MM-DD.md` | Approved test command | Provider returns valid minimal answer |
| P5-T05 | pending | Add oMLX local inference proof test/runbook | `docs/runbooks/omlx.md` | Local runtime command | Real local response captured |
| P5-T06 | pending | Add model routing decision tests | `tests/test_model_routing.py` | `python -m unittest tests.test_model_routing -v` | Local-first and approval escalation pass |
| P5-T07 | pending | Commit model cooperation slice | Adapter, tests, runbook, evidence | `git diff --check` then `git commit` | Commit created |

### P6: Semantica Governed Memory

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P6-T01 | pending | Write failing Semantica adapter health test | `tests/test_semantica_adapter.py` | `python -m unittest tests.test_semantica_adapter -v` | Fails before adapter |
| P6-T02 | pending | Add Semantica adapter skeleton | `forma_ai/semantica_adapter.py` | `python -m unittest tests.test_semantica_adapter -v` | Health test passes |
| P6-T03 | pending | Add candidate memory test | `tests/test_semantica_adapter.py` | `python -m unittest tests.test_semantica_adapter -v` | Fails before candidate flow |
| P6-T04 | pending | Implement candidate memory envelope | `forma_ai/semantica_adapter.py` | `python -m unittest tests.test_semantica_adapter -v` | Candidate flow passes |
| P6-T05 | pending | Add approval-to-commit memory test | `tests/test_semantica_adapter.py` | `python -m unittest tests.test_semantica_adapter -v` | Approval flow passes |
| P6-T06 | pending | Wire task audit event to Semantica adapter | `forma_ai/supervisor.py` | `python -m unittest discover tests -v` | Audit event test passes |
| P6-T07 | pending | Commit governed memory slice | Adapter, supervisor, tests | `git diff --check` then `git commit` | Commit created |

### P7: History, Cancel, Resume, Recovery

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P7-T01 | pending | Write failing persisted task-state test | `tests/test_task_state_store.py` | `python -m unittest tests.test_task_state_store -v` | Fails before store |
| P7-T02 | pending | Implement repository-local task-state store | `forma_ai/task_state_store.py` | `python -m unittest tests.test_task_state_store -v` | Store test passes |
| P7-T03 | pending | Add cancellation persistence test | `tests/test_task_state_store.py` | `python -m unittest tests.test_task_state_store -v` | Cancel state survives reload |
| P7-T04 | pending | Add resume-from-history supervisor test | `tests/test_supervisor_resume.py` | `python -m unittest tests.test_supervisor_resume -v` | Resume route passes |
| P7-T05 | pending | Add UI history/recovery contract | Swift tests | `swift test --package-path prototypes/packaging` | History recovery visible |
| P7-T06 | pending | Run interrupted-task manual recovery proof | `evidence/recovery/recovery-YYYY-MM-DD.md` | Manual scenario | Recovery proof recorded |
| P7-T07 | pending | Commit history/cancel/resume slice | Store, supervisor, Swift, tests, evidence | `git diff --check` then `git commit` | Commit created |

### P8: Distribution and Public-Source Hardening

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P8-T01 | pending | Add public distribution checklist | `docs/distribution/public-release-checklist.md` | `test -f docs/distribution/public-release-checklist.md` | Checklist exists |
| P8-T02 | pending | Add license notice collection task | `docs/distribution/notices.md` | `test -f docs/distribution/notices.md` | Notices started |
| P8-T03 | pending | Add secrets scan command to release checklist | Release docs | Release command documented | Secrets gate explicit |
| P8-T04 | pending | Add clean-install acceptance runbook | `docs/runbooks/clean-install.md` | `test -f docs/runbooks/clean-install.md` | Runbook exists |
| P8-T05 | pending | Add novice-user acceptance script | `docs/runbooks/novice-acceptance.md` | `test -f docs/runbooks/novice-acceptance.md` | Script exists |
| P8-T06 | pending | Run final test suite | Repo | Python and Swift test commands | Tests pass |
| P8-T07 | pending | Commit distribution hardening | Distribution docs and tests | `git diff --check` then `git commit` | Commit created |

## Mandatory Completion Update Format

After each task, update the row status and append a short note here:

```text
YYYY-MM-DD HH:mm Asia/Shanghai - TASK-ID - executor - result - evidence - commit-or-none - next TASK-ID
```

## Completion Notes

- 2026-08-31 -- P0-T01/P0-T02/P0-T03 verified by Codex root agent. Created master tracker, handoff document, and updated `AGENTS.md`.
- 2026-08-31 -- P0-T04 verified by Codex root agent. `git diff --check` passed for documentation-control files.
- 2026-08-31 -- P0-T05 verified by Codex root agent. Commit `3756677` includes only `AGENTS.md`, this tracker, and `docs/TASK_HANDOFF.md`.
- 2026-08-31 -- P0-T05 follow-up verified by Codex root agent. Commit `7b516a1` records completion progress for the control documents.
- 2026-08-31 -- P0-T06 verified by Codex root agent. This status update is committed and pushed together with the governance documentation chain.
- 2026-08-31 01:57 Asia/Shanghai - P0-T07 - Codex root agent - reconciled role conflicts and enforced upstream-first reuse - repository-wide conflict scan and `git diff --check` passed - commit `a618993` plus closeout record - next P1-T01
- 2026-08-31 05:57 Asia/Shanghai - P0-T08 - Codex root agent - renamed tracked product identity to Forma AI and integrated original macOS icon - legacy-name scan, 225 Python tests, 30 Swift tests, signed bundle/icon inspection passed - commit `7068cba` plus closeout record - next P1-T01
- 2026-08-31 - P1-T01 - Codex root agent - inventoried local four-upstream sources, declared pins, installed artifacts, and exact gaps - repository/local read-only scans plus oMLX bundle and active-record inspection - commit pending closeout - next P1-T02
- 2026-08-31 - P1-T02 - Codex root agent - refreshed Semantica v0.6.7 capabilities and reuse boundary - official tag/release/manifest/pinned-source evidence and repository scan - commit pending closeout - next P1-T03
- 2026-08-31 - P1-T03 - Codex root agent - mapped holaOS at commit `4684714ee133794cdbb86630e42b7d93447fb2e2` - official repository, README, license, workspace, runtime, and package-tree evidence - commit pending closeout - next P1-T04
- 2026-08-31 - P1-T04 - Codex root agent - mapped Herdr v0.8.2 CLI/socket, event, lifecycle, resume, recovery, and handoff surfaces - official immutable release, pinned source, schema, and documentation evidence - commit pending closeout - next P1-T05
- 2026-08-31 - P1-T05 - Codex root agent - refreshed oMLX v0.6.3 tag, release, artifact, API, dependency, model-capability, and layered inference evidence; corrected stale runbook claim - official pinned source plus repository evidence - 24 targeted tests passed - commit pending closeout - next P1-T06
- 2026-08-31 - P1-T06 - Codex root agent - separated private development, public source, copied-source, binary, adapter, and commercial release modes; bound all four reviewed revisions and explicit notice/trademark/provenance gates - matrix scan and whitespace check passed - commit pending closeout - next P1-T07
- 2026-08-31 - P1-T07 - Codex root agent - recorded four evidence-linked upstream reuse decisions with integration mode, product boundary, duplication stop, validation gate, and distribution consequence - four-record and whitespace checks passed - commit pending closeout - next P1-T08
- 2026-08-31 - P1-T08 - Codex root agent - audited the complete seven-commit upstream inventory chain, verified all P1 evidence files and four reuse decisions, confirmed documentation-only scope and origin/main synchronization - phase P1 verified - next P2-T01
- 2026-08-31 - P2-T01 - Codex root agent - added vendor-neutral adapter identity and layered health-envelope contract tests - expected `ModuleNotFoundError: forma_ai.adapter_contract` observed before implementation - commit pending closeout - next P2-T02
- 2026-08-31 - P2-T02 - Codex root agent - implemented immutable adapter identity and layered health envelopes with deterministic serialization - 2 targeted tests passed and whitespace check passed - commit pending closeout - next P2-T03
- 2026-08-31 - P2-T03 - Codex root agent - added the vendor-neutral capability declaration red test for stable operation names and proof level - expected missing `CapabilityDeclaration` import observed - commit pending closeout - next P2-T04
- 2026-08-31 - P2-T04 - Codex root agent - implemented the immutable capability declaration with JSON-compatible ordered operations and proof level - 3 targeted tests passed - commit pending closeout - next P2-T05
- 2026-08-31 - P2-T05 - Codex root agent - added red tests binding exact policy payload/approval fields and correlated redaction-explicit audit fields - expected missing `AuditEnvelope`/`PolicyPreview` boundary observed - commit pending closeout - next P2-T06
- 2026-08-31 - P2-T06 - Codex root agent - implemented immutable exact-payload policy preview and redaction-explicit audit envelopes without raw payload fields - 5 targeted contract tests passed - commit pending closeout - next P2-T07
- 2026-08-31 - P2-T07 - Codex root agent - specified and machine-tested the universal Codex/Claude/compatible-agent lifecycle contract with Herdr authority, recovery, policy, audit, artifact, idempotency, and conformance rules - 9 combined contract tests passed - committed/pushed as `2b5227c` - next P2-T08
