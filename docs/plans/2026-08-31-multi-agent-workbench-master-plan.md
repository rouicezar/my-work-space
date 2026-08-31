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
- The mandatory Chinese mirrors are stored in the user-approved MyNote `00_资源库/11_项目开发/Forma AI` folder. This English tracker remains authoritative, but every task takeover and closeout must synchronize task ID, status, evidence, commit/push state, blocker, and next action to the Chinese progress and handoff mirrors. Any mismatch blocks new product work until repaired.
- On Codex quota warning, stop opening new work, close and verify the smallest safe unit, update both control documents, commit and push verified work, and leave a clean repository. Preserve and explicitly inventory any pre-existing dirty work that cannot safely be removed.

## Current State

Updated: 2026-08-31 Asia/Shanghai
Current phase: P4 independent workbench product experience
Current task: P4-T07
Current status: pending
Next action: implement the complete eight-section Settings information architecture while keeping setup and recovery separate from normal product settings.

Completed parallel task: P4-T04
Parallel status: verified; the dedicated task produced no P4-T05 changes before primary takeover
Parallel next action: remain stopped until the primary task closes P4-T05.

Current Git fact at P2-T08 takeover:

- `main` was clean and synchronized with `origin/main` at `5061ba7`; there were no uncommitted paths to preserve.

Historical interrupted-work inventory retained for recovery context only (this is not a statement about the current worktree and does not establish current ownership):

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
| CAP-05 | Cloud model setup | DeepSeek/OpenAI-compatible providers | Settings has provider list, credential state, low-cost test, and removal | partial | Historical DeepSeek/settings work is recorded; current implementation and real-call evidence remain to be revalidated in P5 |
| CAP-06 | Governed memory | Semantica | Retrieval, candidate memory, approval, audit | not_started | None |
| CAP-07 | History and recovery | Product workbench | Task history, failed run recovery, cancel/resume | partial | Sidebar exists; user reports unclear product function |
| CAP-08 | Tool/process console | Herdr | Task execution logs and external tool lifecycle | not_started | None |
| CAP-09 | Permission and audit | Product policy layer | External writes and cloud calls require preview/approval/audit | partial | Policy intent exists; full UI not verified |
| CAP-10 | Distribution readiness | Packaging/lifecycle | Clean install, upgrade, rollback, uninstall, recovery gates | partial | Packaging tests exist; product experience incomplete |
| CAP-11 | Universal agent adapters | Codex/Claude/compatible tools | Capability discovery, dispatch, status, handoff, cancel, resume, artifacts, audit | mapped | Generic contract: `docs/contracts/agent-adapter.md`; concrete runtime conformance remains pending in P3 and later adapter tasks |
| CAP-12 | Complete product settings | Product workbench | General, providers, agents/tools, memory, permissions, runtime, privacy, diagnostics/recovery | not_started | Current screen is setup/recovery only |

## Milestone Tracker

| Phase | Goal | Status | Exit Gate |
|---|---|---|---|
| P0 | Correct governance and stop product drift | verified | Tracker, handoff, role documents, and upstream-first reuse rules agree |
| P1 | Inventory upstream capabilities and licenses | verified | Reuse decisions for all four upstreams have evidence |
| P2 | Freeze the vendor-neutral adapter protocol and assign concrete conformance gates | verified | Generic identity, health, capability, policy, audit, and agent-lifecycle contracts pass machine tests; every concrete adapter has a named downstream conformance owner |
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
| P0-T09 | verified | Create and govern synchronized Chinese mirrors of the execution tracker and handoff | `AGENTS.md`, both English control docs, user-approved MyNote Forma AI folder | existence, required-anchor, state-parity, and `git diff --check` checks | Two Chinese documents exist and every future task exit must synchronize both language sets |

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
| P2-T08 | verified | Audit and close the generic adapter-contract phase without claiming concrete adapter conformance | Adapter contract, agent contract, tests, tracker, handoff | Contract tests plus `git diff --check` | Generic contract gate is truthful and concrete conformance has named downstream owners |

Concrete adapter conformance is deliberately outside the P2 completion claim. A protocol document or generic unit test cannot make a concrete adapter compatible. The following ownership is mandatory, and the corresponding phase cannot close until its real or faithfully mockable boundary tests pass:

| Concrete boundary | Downstream owner | Required evidence before conformance may be claimed |
|---|---|---|
| Herdr plus Codex/Claude/compatible agent execution | P3-T01 through P3-T09 | Official CLI/socket/API discovery, two parallel tasks, stable states, cancel, resume, reconnect/recovery, artifacts, and audit mapping |
| Separately installed holaOS non-visual interface | P4-T07A | Upstream entry point and license decision plus identity/health/capability smoke test through the generic contract; no uncleared frontend/assets bundled |
| oMLX local inference and DeepSeek/OpenAI-compatible cloud execution | P5-T01 through P5-T07 | Real oMLX completion or embedding response; credential state, preview, explicit approval, low-cost DeepSeek response, routing decision, and audit evidence |
| Semantica governed memory | P6-T01 through P6-T07 | Health, retrieval/candidate, approval-to-commit, provenance, and audit-event contract tests against the selected upstream boundary |

P2 completion never waives these gates and must not be cited as evidence that any concrete adapter is implemented or verified.

### P3: Herdr Core Multi-Agent Runtime

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P3-T01 | verified | Write failing Herdr adapter availability test | `tests/test_herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Fails before adapter exists |
| P3-T02 | verified | Add Herdr adapter skeleton using adapter contract | `forma_ai/herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Availability test passes |
| P3-T03 | verified | Write failing test for spawning two mock tasks | `tests/test_herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Fails on missing spawn |
| P3-T04 | verified | Implement mockable task spawn/status methods | `forma_ai/herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Two tasks have stable IDs and states |
| P3-T05 | verified | Write failing test for cancel and resume envelope | `tests/test_herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Fails on missing lifecycle |
| P3-T06 | verified | Implement cancel/resume mapping | `forma_ai/herdr_adapter.py` | `python -m unittest tests.test_herdr_adapter -v` | Lifecycle tests pass |
| P3-T07 | verified | Wire supervisor to Herdr adapter behind feature flag | `forma_ai/supervisor.py` | `python -m unittest discover tests -v` | Existing tests pass |
| P3-T08 | verified | Add UI task state fixture for parallel agents | `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift` | `swift test --package-path prototypes/packaging` | Swift tests pass |
| P3-T09 | verified | Commit Herdr core slice | Adapter, supervisor, tests, Swift fixture | `git diff --check` then `git commit` | Commit created |

### P4: Independent Workbench Product Experience

| ID | Status | Action | Files | Command | Expected Evidence |
|---|---|---|---|---|---|
| P4-T01 | verified | Write UI contract test for first-screen task composer | `prototypes/packaging/Tests/LifecycleContractTests/ProductManifestTests.swift` | `swift test --package-path prototypes/packaging` | Baseline 30 tests passed with 2 skipped; new target fails because `WorkbenchSurfaceContract` is absent |
| P4-T02 | verified | Move daily work surface above setup/recovery | `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift` | `swift test --package-path prototypes/packaging` | Target contract passed; full Swift package passed 31 tests with 2 real-Keychain tests skipped |
| P4-T03 | verified | Add model/provider selection contract | Lifecycle contract tests | `swift test --package-path prototypes/packaging` | Filtered test fails because `WorkbenchSurfaceContract` has no `modelSelection` member |
| P4-T04 | verified | Implement cloud/local model selector state | Swift app and manifest files | `swift test --package-path prototypes/packaging` | Selector target passed; full Swift package passed 32 tests with 2 real-Keychain tests skipped |
| P4-T05 | verified | Add task history visible state contract | Swift tests | `swift test --package-path prototypes/packaging` | Target history test passed; full Swift package passed 33 tests with 2 real-Keychain skips |
| P4-T06 | verified | Add recovery action visible state contract | Swift tests | `swift test --package-path prototypes/packaging` | Target recovery test passed; full Swift package passed 34 tests with 2 real-Keychain skips |
| P4-T07 | pending | Add complete Settings information architecture and contracts | Swift app, manifest, and tests | `swift test --package-path prototypes/packaging` | All eight settings sections are reachable and setup/recovery is separated |
| P4-T07A | pending | Verify the separately installed holaOS non-visual adapter boundary | holaOS adapter, tests, and capability/reuse ledger | Targeted adapter conformance test plus upstream entry-point audit | Generic identity, health, and capability smoke test passes without bundling uncleared UI/assets |
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
- 2026-08-31 - P2-T08 - Codex root agent - replaced stale current-dirty claims with verified Git fact, narrowed P2 to the generic protocol boundary, and assigned concrete Herdr, holaOS, oMLX/DeepSeek, and Semantica conformance gates downstream - 9 combined contract tests, ownership scan, and `git diff --check` passed - committed/pushed as `a6b701d` plus closeout record - next P3-T01
- 2026-08-31 - P3-T01 - Codex root agent - added Herdr binary-availability contract tests that distinguish missing from discovered-only state without claiming reachability or readiness - expected `ModuleNotFoundError: forma_ai.herdr_adapter` observed before implementation - committed/pushed as `6fc033b` - next P3-T02
- 2026-08-31 - P3-T02 - Codex root agent - implemented a thin injected Herdr binary-discovery adapter using generic identity and layered health envelopes, with discovered-only state remaining not reachable and not ready - 11 targeted Herdr and protocol tests plus `git diff --check` passed - committed/pushed as `5b4584d` plus closeout record - next P3-T03
- 2026-08-31 - P0-T09 - Codex root agent - created Chinese operational mirrors of the progress tracker and handoff in the user-approved MyNote folder and made bilingual parity a mandatory takeover/exit gate - file, anchor, state-parity, and `git diff --check` checks passed; optional GBrain refresh was not run because required preflight found 2584 stale chunks - committed/pushed as `66434ff` plus closeout records - next P3-T03
- 2026-08-31 - P3-T03 - Codex root agent - added the two-mock-task Herdr spawn/status red test with stable task/run/pane IDs, independent state reads, and revision evidence - expected `TypeError` on missing injectable request boundary observed while two prior tests stayed green - committed/pushed as `e652ed2` - next P3-T04
- 2026-08-31 - P3-T04 - Codex root agent - implemented and then corrected immutable Herdr task envelopes plus injected `agent.start`/`agent.get` translation to exact pinned protocol 20 `AgentStartParams`, `agent_started`, and `agent_info` shapes while leaving state authority upstream - schema-conformant red/green correction plus 12 Herdr/generic protocol tests and `git diff --check` passed - initial commit `2d56064`, corrective commit `e6c4106`, both pushed - next P3-T05
- 2026-08-31 - P3-T05 - Codex root agent - added protocol-grounded red tests for exact-pane graceful cancel and native-session resume with session/revision reconciliation before schema-valid restart - 3 existing Herdr tests passed and 2 new tests failed as expected on missing lifecycle methods - committed/pushed as `db9c0ee` plus closeout record - next P3-T06
- 2026-08-31 - P3-T06 - Codex root agent - recovered the exact P3-T05 breakpoint and implemented exact-pane graceful cancel plus fail-closed native-session resume with revision/session reconciliation before schema-valid restart - 14 Herdr/generic protocol tests, integrated P4 Swift package 31 passed with 2 real-Keychain skips, and `git diff --check` passed - rebased after P4-T03 as implementation `9616aa1`, closeout `2fdd62b`, plus final sync record - next P3-T07
- 2026-08-31 - P3-T07 - Codex root agent - added an explicit default-off Supervisor feature boundary that delegates enabled execution exactly once to `HerdrAdapter.spawn_task` without copying runtime state - focused 2 tests and restored full Python suite 242 tests passed with 1 opt-in Semantica integration skip; initial sandbox-only temp-directory errors were cleared by the authorized rerun - commit and push recorded in the paired handoff - next P3-T08
- 2026-08-31 - P3-T08/P3-T09 - Codex root agent - added preview-injected parallel Agent cards with stable task/run/pane identities, running and blocked states, and an explicit non-runtime-evidence label while production defaults to an empty Agent list - Swift package 32 tests passed with 2 real-Keychain skips, source boundary inspection and `git diff --check` passed - committed/pushed in the paired handoff - P3 complete; next P4-T05
- 2026-08-31 - P4-T05 - Codex root agent - corrected the invalid permanent-red closeout after Swift target compilation proved it blocked later contract tests; implemented only the history truth-boundary contract for primary navigation, persisted-task sourcing, explicit empty state, and no preview fixtures - target test passed and full Swift package passed 33 tests with 2 real-Keychain skips; no persistence or fake rows added - next P4-T06
- 2026-08-31 - P4-T06 - Codex root agent - added a recovery visibility red contract for task-detail placement, blocked/failed/interrupted/unknown states, persisted verified-session resume, fresh snapshot/revision reconciliation, and separately approved force termination - filtered test failed exactly because `WorkbenchSurfaceContract` lacks `recovery`; dependent enum inference errors were consequential - committed/pushed in the paired handoff - next P4-T07
- 2026-08-31 - P4-T06 correction - Codex root agent - implemented only the pure recovery visibility contract required to prevent a permanent compile-red blocker before P4-T07 - target recovery test passed and full Swift package passed 34 tests with 2 real-Keychain skips; no recovery UI, persistence, or lifecycle authority was invented - next P4-T07
