# Forma AI Task Handoff

This is the authoritative handoff document for agent takeover, interruption recovery, and cross-tool continuity.

Every agent must read this file, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, and `AGENTS.md` before changing product code.

## Handoff Rules

- Claim exactly one task ID from the master plan before editing.
- Update the master plan and this handoff before ending a turn, even if the task is blocked.
- Never mark work complete without commands, test output, artifact evidence, or an explicit reason why verification was impossible.
- Preserve unrelated dirty work. Do not revert or overwrite changes made by another agent or by the user.
- Do not write secrets, API keys, full prompts containing credentials, or private account data into this file.
- For cloud providers, record provider name, policy decision, approximate cost boundary, result class, and correlation ID if available. Do not record keys.
- For screenshots, record what the screenshot actually proves. Do not treat a wrong-window or background capture as UI evidence.
- If an external agent, tool, or parallel task takes over, it must add a takeover entry before work and an exit entry after work.
- A Codex quota warning triggers immediate closeout: start no new work, verify the smallest safe unit, update tracker and handoff, commit and push, and confirm repository cleanliness. Never discard unrelated dirty work merely to make status clean; inventory and isolate it instead.

## Current Baton

Updated: 2026-08-31 Asia/Shanghai
Owner: Codex root agent
Master plan task: P2-T08
State: P2-T07 universal AI-agent contract verified; contract commit and push pending
Next required action: commit/push P2-T07, then audit and close the complete P2 adapter-contract phase.

## Product Goal Snapshot

The product is a local-first, multi-agent Mac AI workbench.

- Product-owned native workbench is the default distributable UI.
- holaOS is a capability/workflow reference and optional separately installed adapter until redistribution is cleared.
- Herdr is the core multi-agent runtime and must support parallel execution, readable state, cancellation, resume, and recovery.
- Semantica is the governed long-term memory and decision-evidence authority.
- oMLX is the local inference runtime and must prove real inference.
- Cloud models are optional, explicit, credential-gated, approval-gated, and audited.

## Dirty Worktree at This Handoff

These paths were already dirty before the documentation-control task and must be preserved:

- `forma_ai/deepseek_adapter.py`
- `tests/test_deepseek_adapter.py`
- `prototypes/packaging/Sources/LifecycleContract/ProductManifest.swift`
- `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift`
- `prototypes/packaging/Tests/LifecycleContractTests/ProductManifestTests.swift`
- `build/`
- `evidence/ui/cloud-settings-review-2026-08-31.png`

Do not include these implementation changes in the governance-doc commit unless a later task explicitly claims and verifies them.

## Interrupted Work Summary

DeepSeek/cloud setup work was in progress before this handoff:

- Dedicated DeepSeek credentials were configured by the user in the project.
- The conversation UI still did not provide a usable task/chat experience.
- The DeepSeek adapter had uncommitted changes around urllib opener timeout handling and unexpected error classification.
- A real DeepSeek attempt reached the provider but ended as `DEEPSEEK_RESPONSE_INVALID`.
- The likely hypothesis was an output-budget/thinking-mode interaction, but that is not verified.
- A true low-cost DeepSeek closed loop remains open under master-plan task P5-T04.

Settings/workbench work was in progress before this handoff:

- Cloud settings were being moved toward a clearer product settings flow.
- User feedback shows the current Settings & Recovery page behaves like initialization/recovery, not like a full product settings surface.
- The current visible product shape is insufficient: New task, History, and Settings & Recovery do not yet explain or deliver the target workbench.
- Future UI work must make the first screen a usable multi-agent task workbench, not a diagnostic panel.

Previously reported local verification that must be revalidated before relying on it:

- `swift test --package-path prototypes/packaging`: 30 passed, 2 skipped.
- Targeted Python DeepSeek/Supervisor tests: 43 passed.
- `evidence/ui/cloud-settings-review-2026-08-31.png` did not prove the foreground app state and must not be treated as acceptance evidence.

## Takeover Checklist

1. Read `AGENTS.md`.
2. Read `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`.
3. Read this file.
4. Inspect current git status.
5. Choose the next `pending` task from the master plan unless the user gives a different task.
6. Change that task to `in_progress` in the master plan.
7. Add a takeover entry here.
8. Do the smallest verifiable unit of work.
9. Run the listed verification.
10. Update both documents with result, evidence, commit status, and next action.

## Entry Template

```text
## YYYY-MM-DD HH:mm Asia/Shanghai - TASK-ID - takeover|exit

Executor:
Starting git state:
Scope:
Files intended:
Actions:
Verification:
Evidence:
Files changed:
Commit:
Push:
Decisions:
Assumptions:
Blocked items:
Next exact action:
Approval needed:
Secret/external-write status:
Quota state and closeout action:
```

## Handoff Log

## 2026-08-31 - P2-T07 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `026e9da`
Scope: specify a vendor-neutral AI-agent adapter for Codex, Claude, and compatible terminal/API tools
Files intended: contract document, contract tests, master tracker, and handoff
Actions: defined normative discover/dispatch/status/handoff/cancel/resume/artifacts/audit operations; fixed Herdr execution authority, reconnect/revision/idempotency behavior, secret/policy/audit boundaries, and minimum conformance evidence
Verification: `python3 -m unittest tests.test_agent_adapter_contract tests.test_adapter_contract -v` passed 9 tests; `git diff --check` passed
Evidence: contract document plus machine checks for all operations, runtime/memory authority, cancellation/recovery, approval/audit, artifacts, and parallel-run conformance
Files changed: `docs/contracts/agent-adapter.md`, `tests/test_agent_adapter_contract.py`, master tracker, and handoff
Commit: pending contract commit
Push: pending
Decisions: adapter implementations translate to Herdr rather than replacing it; unknown/disconnected/blocked states never become success; force cancellation and external writes remain approval-gated
Assumptions: concrete Codex/Claude adapters will prove this same contract in later implementation tasks
Blocked items: none for specification; concrete runtime conformance remains later work
Next exact action: commit/push P2-T07, then claim P2-T08
Approval needed: none
Secret/external-write status: no secrets; repository-local docs/tests only
Quota state and closeout action: no warning; verified contract unit ready to push

## 2026-08-31 - P2-T07 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `026e9da`
Scope: specify a vendor-neutral AI-agent adapter for Codex, Claude, and compatible terminal/API tools
Files intended: `docs/contracts/agent-adapter.md`, contract tests, master tracker, and handoff
Actions: claimed P2-T07 in plan order
Verification: pending contract validation test
Evidence: Herdr v0.8.2 capability ledger, holaOS harness map, and P2 identity/capability/policy/audit envelopes
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: contract covers discover, dispatch, status, handoff, cancel, resume, artifacts, audit and reconnect semantics; Herdr remains execution authority
Assumptions: document requirements can be machine-checked before concrete adapter implementations exist
Blocked items: none
Next exact action: inspect contract/test layout, create the specification and its validation test, then run it
Approval needed: none
Secret/external-write status: no secrets; repository-local docs/tests only
Quota state and closeout action: no warning; close and push current unit on warning

## 2026-08-31 - P2-T06 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `69a21cc`
Scope: implement only the policy-preview and audit envelopes required by P2-T05
Files intended: adapter contract, master tracker, and handoff
Actions: added immutable `PolicyPreview` and `AuditEnvelope` with deterministic JSON-compatible serialization and no raw payload field
Verification: adapter contract suite passed 5 tests; `git diff --check` passed
Evidence: targeted unittest output
Files changed: adapter contract, master tracker, and handoff
Commit: pending implementation commit
Push: pending
Decisions: policy preview binds digest and approval boundary; audit records only correlation/action/outcome/time/redaction metadata
Assumptions: stricter value validation can be introduced by a later explicit contract revision
Blocked items: none
Next exact action: commit/push P2-T06, then claim P2-T07
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; verified unit ready to push

## 2026-08-31 - P2-T06 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `69a21cc`
Scope: implement only the policy-preview and audit envelopes required by P2-T05
Files intended: adapter contract, master tracker, and handoff
Actions: claimed P2-T06 in plan order
Verification: pending targeted unittest
Evidence: P2-T05 red tests
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: immutable envelopes and explicit tuple-to-list serialization; no raw payload content field
Assumptions: field validation remains outside this minimal planned slice
Blocked items: none
Next exact action: add the two dataclasses and run contract tests
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; close and push current unit on warning

## 2026-08-31 - P2-T05 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `a012fcd`
Scope: define intentionally failing policy-preview and audit-envelope contract tests
Files intended: test, master tracker, and handoff
Actions: added exact payload digest/data-class/external-write/approval preview contract and correlated outcome/timestamp/redacted-field audit contract; added no implementation
Verification: targeted unittest failed at intended boundary with missing `AuditEnvelope` import; `PolicyPreview` is also intentionally absent
Evidence: unittest output and two red tests
Files changed: test, master tracker, and handoff
Commit: pending red-test commit
Push: pending
Decisions: raw payload, prompt, and credential values are absent from the audit envelope by construction
Assumptions: tuple fields serialize as ordered JSON lists
Blocked items: none; failure intentional
Next exact action: commit/push P2-T05, then claim P2-T06
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; red unit ready to push

## 2026-08-31 - P2-T05 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `a012fcd`
Scope: define intentionally failing policy-preview and audit-envelope contract tests
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T05 in plan order and reconciled the prior baton with pushed P2-T04
Verification: pending expected failing unittest
Evidence: product approval/audit rules and existing cloud proposal/audit implementations
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: preview binds exact payload digest, data classes, external-write and approval state; audit stores correlation/action/outcome/timestamp and names redacted fields without payload content
Assumptions: event and correlation IDs remain opaque in this minimal contract slice
Blocked items: none
Next exact action: add red tests and capture the missing-symbol failure
Approval needed: none
Secret/external-write status: no secrets; repository-local tests only
Quota state and closeout action: no warning; close and push current red unit on warning

## 2026-08-31 - P2-T04 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `61b4aef`
Scope: implement only the capability declaration required by P2-T03
Files intended: adapter contract, master tracker, and handoff
Actions: added immutable `CapabilityDeclaration`; converted tuple operations to an ordered JSON-compatible list
Verification: targeted adapter contract suite passed 3 tests; `git diff --check` passed
Evidence: unittest output
Files changed: `forma_ai/adapter_contract.py`, master tracker, and handoff
Commit: pending implementation commit
Push: pending
Decisions: declarations report capability evidence but do not assert successful runtime execution
Assumptions: validation constraints will be introduced only through later explicit tests
Blocked items: none
Next exact action: commit/push P2-T04, then claim P2-T05
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; verified unit ready to push

## 2026-08-31 - P2-T04 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `61b4aef`
Scope: implement only the capability declaration required by P2-T03
Files intended: `forma_ai/adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T04 in plan order
Verification: pending targeted unittest
Evidence: P2-T03 expected missing-symbol failure
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: immutable declaration; tuple operations serialize to a JSON-compatible ordered list
Assumptions: field validation remains outside this planned minimal slice
Blocked items: none
Next exact action: implement the dataclass and run the adapter contract tests
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; close and push on warning

## 2026-08-31 - P2-T03 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `947268d`
Scope: define the intentionally failing capability-declaration contract test
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: added a vendor-neutral `agent_execution` declaration requiring deterministic `dispatch`, `status`, `cancel`, and `resume` operations plus proof level; added no implementation
Verification: targeted unittest failed at the intended boundary: `ImportError: cannot import name 'CapabilityDeclaration'`
Evidence: unittest output and test contract
Files changed: test, master tracker, and handoff
Commit: pending red-test commit
Push: pending
Decisions: declaration reports supported operations and evidence; it does not imply runtime success
Assumptions: tuple order is retained in serialized output
Blocked items: none; failure is intentional
Next exact action: commit/push P2-T03, then claim P2-T04
Approval needed: none
Secret/external-write status: no secrets
Quota state and closeout action: no warning; red-test unit ready to push

## 2026-08-31 - P2-T03 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `947268d`
Scope: define the intentionally failing capability-declaration contract test
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T03 in plan order and reconciled the prior baton with the already pushed P2-T02 commit
Verification: pending expected failing unittest result
Evidence: P2-T01/T02 identity and health contract plus upstream capability ledgers
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: capability declaration is vendor-neutral and names stable operations plus evidence level; implementation belongs only to P2-T04
Assumptions: operation order is part of deterministic serialized output for this minimal slice
Blocked items: none
Next exact action: add the test and capture the expected missing-symbol failure
Approval needed: none
Secret/external-write status: no secrets; repository-local test only
Quota state and closeout action: no warning; close and push this red-test unit if a warning appears

## 2026-08-31 - P2-T02 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `0df9d25`
Scope: implement only the adapter identity and health-envelope dataclasses required by P2-T01
Files intended: `forma_ai/adapter_contract.py`, master tracker, and handoff
Actions: added immutable `AdapterIdentity` and `HealthEnvelope` dataclasses with deterministic `to_dict` serialization; added no capability or policy surface
Verification: `python3 -m unittest tests.test_adapter_contract -v` passed 2 tests; `git diff --check` passed
Evidence: targeted unittest output
Files changed: `forma_ai/adapter_contract.py`, master tracker, and this handoff
Commit: pending implementation commit
Push: pending
Decisions: minimal implementation preserves the red-test boundary and defers validation/capability/policy behavior to their planned tests
Assumptions: opaque strings are sufficient for the current contract slice
Blocked items: none
Next exact action: commit/push P2-T02, then claim P2-T03
Approval needed: none
Secret/external-write status: no secrets; repository-local code and tests only
Quota state and closeout action: normal; verified unit is ready to commit and push

## 2026-08-31 - P2-T02 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `0df9d25`
Scope: implement only the adapter identity and health-envelope dataclasses required by P2-T01
Files intended: `forma_ai/adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T02 in plan order
Verification: pending targeted unittest
Evidence: P2-T01 red test
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: immutable dataclasses with deterministic dictionary serialization; no capability or policy fields before their own red tests
Assumptions: current string fields remain opaque contract values until later validation tasks require constraints
Blocked items: none
Next exact action: add the minimal module and run `tests.test_adapter_contract`
Approval needed: none
Secret/external-write status: no secrets; repository-local code and tests only
Quota state and closeout action: normal; close and push this implementation unit on warning

## 2026-08-31 - P2-T01 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `f3cd94e`
Scope: add the first intentionally failing contract test for adapter identity and health envelope
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: defined exact stable identity fields and a health envelope that separates reachability, readiness, proof level, timestamp, and reason code; did not add implementation
Verification: `python3 -m unittest tests.test_adapter_contract -v` failed at the intended boundary with `ModuleNotFoundError: No module named 'forma_ai.adapter_contract'`
Evidence: unittest output and the new two-test contract file
Files changed: `tests/test_adapter_contract.py`, master tracker, and this handoff
Commit: pending red-test commit
Push: pending
Decisions: identity is vendor-neutral and versioned; health cannot collapse reachable, ready, and real proof into one boolean
Assumptions: P2-T02 will implement only the surface demanded by these tests
Blocked items: none; failure is intentional and required by the plan
Next exact action: commit/push P2-T01, then claim P2-T02
Approval needed: none
Secret/external-write status: no secrets; repository-local test only
Quota state and closeout action: normal; red-test unit is ready to commit and push

## 2026-08-31 - P2-T01 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `f3cd94e`
Scope: add the first intentionally failing contract test for adapter identity and health envelope
Files intended: `tests/test_adapter_contract.py`, master tracker, and handoff
Actions: claimed P2-T01 in plan order
Verification: pending expected failing unittest result
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: test only stable vendor-neutral identity and health fields; implementation belongs to P2-T02 and must not be added in this task
Assumptions: an import failure is too coarse; the test should import a named contract surface and then fail because that module is absent
Blocked items: none
Next exact action: inspect local test conventions, create the minimal contract test, and capture the expected failure
Approval needed: none
Secret/external-write status: no secrets; repository-local test only
Quota state and closeout action: normal; close and push this test unit on warning

## 2026-08-31 - P1-T08 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `0de31a5`
Scope: audit and close the complete P1 upstream inventory documentation chain
Files intended: master tracker and handoff only
Actions: verified P1-T01 through P1-T07 status, required evidence files, four decision records, seven scoped commits, origin/main synchronization, whitespace, and pre-close repository state
Verification: all four research/evidence files exist; exactly four reuse decisions exist; no P1-T01 through P1-T07 task remains pending/in-progress/blocked; `git log` shows commits `b799a63`, `64bb3a9`, `fcf9308`, `85f7e54`, `7e42050`, `a7062e5`, and `0de31a5`; `origin/main...HEAD` was empty; `git diff --check` passed
Evidence: repository files, master tracker, decision log, local Git history, and remote-tracking comparison
Files changed: master tracker and this handoff
Commit: pending phase-close documentation commit
Push: pending
Decisions: individual scoped commits satisfy the inventory commit requirement and preserve reviewable history; P1 exit gate is met
Assumptions: remote-tracking `origin/main` reflects the successful push immediately preceding this audit
Blocked items: none
Next exact action: commit/push P1 closeout, then claim P2-T01
Approval needed: none
Secret/external-write status: no secrets; Git push only
Quota state and closeout action: normal; phase closeout is ready to commit and push

## 2026-08-31 - P1-T08 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `0de31a5`
Scope: audit and close the complete P1 upstream inventory documentation chain
Files intended: master tracker and handoff only if the existing inventory commits and evidence pass
Actions: claimed P1-T08 in plan order
Verification: pending status/file/history/push/cleanliness audit
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: P1 closes only if P1-T01 through P1-T07 are verified, evidence files exist, commits contain scoped documentation, and origin/main contains the chain
Assumptions: individual verified task commits satisfy the P1-T08 inventory commit intent; this task records the aggregate audit rather than squashing history
Blocked items: none
Next exact action: run aggregate P1 evidence, history, remote, and cleanliness checks
Approval needed: none
Secret/external-write status: no secrets; repository-local and Git metadata checks only
Quota state and closeout action: normal; close and push this phase audit on warning

## 2026-08-31 - P1-T07 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `a7062e5`
Scope: record durable, evidence-linked reuse decisions for Semantica, holaOS, Herdr, and oMLX
Files intended: decision log, master tracker, and handoff
Actions: added one explicit record per upstream naming its pinned revision, integration mode, Forma-owned boundary, forbidden duplication, acceptance evidence, and distribution obligations
Verification: exactly four `Reuse decision` records exist; all four upstreams and required boundary/acceptance/public terms are present; `git diff --check` passed
Evidence: P1 capability ledgers, upstream matrix, runbook, and license matrix
Files changed: `docs/decisions.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: these four records operationalize ADR-017 and cannot be overridden by older superseded summaries
Assumptions: exact upstream revisions will be re-reviewed before any later upgrade
Blocked items: none for decision recording; implementation acceptance remains in later phases
Next exact action: commit/push P1-T07, then claim P1-T08
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T07 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `a7062e5`
Scope: record durable, evidence-linked reuse decisions for Semantica, holaOS, Herdr, and oMLX
Files intended: `docs/decisions.md`, master tracker, and handoff
Actions: claimed P1-T07 in plan order
Verification: pending four-decision scan and conflict check
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: each record must name the selected integration mode, product-owned boundary, forbidden duplication, validation gate, and distribution consequence
Assumptions: existing superseded ADR summaries remain historical but cannot override the new records
Blocked items: none
Next exact action: inspect the decision log and add four explicit reuse decisions linked to the P1 ledgers
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T06 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `7e42050`
Scope: reconcile Semantica, holaOS, Herdr, and oMLX license obligations with personal development and future public open-source distribution
Files intended: license matrix, master tracker, and handoff
Actions: bound each component to its reviewed revision; separated private, public-source, copied-source, binary, adapter, and commercial modes; added provenance, notices, SBOM, trademark, asset, model, and dependency gates
Verification: required public/redistribution/holaOS terms plus all reviewed revisions and release-mode gates are present; `git diff --check` passed
Evidence: P1-T02 through P1-T05 upstream ledgers and commit-pinned official license links
Files changed: `docs/research/license-matrix.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: open source and non-commercial are not interchangeable; public Forma source without copied upstream code is the lowest-risk candidate; holaOS frontend/bundling remains blocked without written clearance
Assumptions: matrix is engineering compliance guidance, not legal advice
Blocked items: file-level provenance, third-party notices, SBOM, transitive/model licenses, and written holaOS clarification remain P8 release gates
Next exact action: commit/push P1-T06, then claim P1-T07
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T06 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `7e42050`
Scope: reconcile Semantica, holaOS, Herdr, and oMLX license obligations with personal development and future public open-source distribution
Files intended: `docs/research/license-matrix.md`, master tracker, and handoff
Actions: claimed P1-T06 in plan order
Verification: pending matrix and upstream-ledger conflict scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: public source publication, binary distribution, commercial distribution, trademarks/assets, and separately installed adapters must be treated as distinct release modes
Assumptions: this is an engineering compliance gate, not legal advice
Blocked items: none
Next exact action: inspect and reconcile the license matrix with the pinned upstream evidence already recorded in P1-T02 through P1-T05
Approval needed: none
Secret/external-write status: no secrets; repository-local documentation only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T05 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `85f7e54`
Scope: refresh oMLX v0.6.3 API, runtime, model, release, inference-proof, and adapter-boundary evidence
Files intended: upstream matrix, oMLX runbook, master tracker, and handoff
Actions: resolved the lightweight tag; reviewed official release assets/digests, pinned server routes and package dependencies; reconciled local adapter, broker, manifest, generation, and embedding evidence; corrected the stale runbook statement that deep inference was wholly unverified
Verification: `python3 -m unittest tests.test_omlx_adapter tests.test_manifest -v` passed 24 tests; required commit, artifact digest, API routes, chat proof, embedding boundary, pending gates, and health-contract terms are present; `git diff --check` passed
Evidence: official `jundot/omlx` v0.6.3 tag/release API and pinned `server.py`/`pyproject.toml`; repository generation, embedding, isolation/broker evidence and current adapter/manifest tests
Files changed: `docs/research/upstream-matrix.md`, `docs/runbooks/omlx.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: chat generation is verified only for the exact pinned oMLX/Qwen pair; route availability does not grant model capability; embedding, streaming, cancellation, pressure, sustained concurrency, restart, updater, and complete isolation remain open
Assumptions: prior terminal evidence is valid repository evidence but does not substitute for future native user-flow acceptance
Blocked items: no approved embedding model; no new real-runtime execution was required for this inventory correction
Next exact action: commit/push P1-T05, then claim P1-T06
Approval needed: none
Secret/external-write status: no secrets; public read-only source access and local tests only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T05 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `85f7e54`
Scope: refresh oMLX v0.6.3 API, runtime, model, release, inference-proof, and adapter-boundary evidence
Files intended: `docs/research/upstream-matrix.md`, master tracker, and handoff
Actions: claimed P1-T05 in plan order
Verification: pending official tag/source/API/release inspection and repository adapter scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: health and model listing remain readiness signals only; acceptance requires a real chat completion or embedding response tied to a model ID
Assumptions: exact v0.6.3 artifacts and source must be bound before compatibility claims
Blocked items: none
Next exact action: inspect official repository tag, release assets/digests, API routes and schemas, runtime requirements, and existing Forma integration code
Approval needed: none
Secret/external-write status: no secrets; public read-only source access and local read-only inspection only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T04 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `fcf9308`
Scope: map Herdr v0.8.2 CLI/socket capabilities, multi-agent lifecycle, source entry points, release artifacts, and license obligations
Files intended: `docs/research/herdr-capability-ledger.md`, master tracker, and handoff
Actions: resolved the annotated tag to its commit; reviewed immutable release assets/digests, Cargo manifest, Apache license, pinned source tree, bundled protocol schema, socket API, and session/recovery semantics
Verification: ledger exists; exact commit and macOS digest, snapshot/events, parallel dispatch, prompt/wait, state, cancel policy gap, native resume, restart recovery, handoff, security, source entry points, and validation gaps are present; `git diff --check` passed
Evidence: official `herdrdev/herdr` v0.8.2 tag/release API and commit-pinned README, Cargo manifest, LICENSE, recursive source tree, socket API, session-state documentation, and API schema
Files changed: `docs/research/herdr-capability-ledger.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: integrate the verified official binary through CLI and local socket; Herdr remains the mandatory runtime authority while Forma AI owns policy, orchestration intent, UI, and audit
Assumptions: upstream protocol surfaces remain unaccepted until the exact binary is downloaded, digest-verified, and exercised locally
Blocked items: no local runtime test yet; cancellation requires a Forma policy over pane/process controls because no single high-level `agent.cancel` appeared in the reviewed map
Next exact action: commit/push P1-T04, then claim P1-T05
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T04 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `fcf9308`
Scope: map Herdr v0.8.2 CLI/socket capabilities, multi-agent lifecycle, source entry points, release artifacts, and license obligations
Files intended: `docs/research/herdr-capability-ledger.md`, master tracker, and handoff
Actions: claimed P1-T04 in plan order
Verification: pending official tag/source/protocol/release/license inspection and ledger completeness scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: Herdr remains the required core execution runtime; the ledger must prevent cosmetic or product-owned replacement of upstream multi-agent lifecycle behavior
Assumptions: v0.8.2 must resolve to an immutable commit and artifacts before integration
Blocked items: none
Next exact action: inspect official repository metadata, tag, release assets, source tree, CLI/socket documentation, Cargo manifest, and license
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T03 - exit

Executor: Codex root agent
Starting git state: clean after pushed commit `64bb3a9`
Scope: map holaOS capabilities, source entry points, non-visual reuse candidates, visual/branding exclusions, and distribution obligations
Files intended: `docs/research/holaos-capability-ledger.md`, master tracker, and handoff
Actions: reviewed official commit, repository/workspace shape, runtime and package entry points, README claims, and modified license; recorded a granular upstream-first reuse boundary
Verification: ledger exists; required revision, runtime/package entry points, license/public-distribution boundary, Semantica memory authority, Herdr role, and open validation gaps are present; `git diff --check` passed
Evidence: official `holaboss-ai/holaOS` repository API and commit-pinned README, LICENSE, root manifest, runtime tree, and packages tree at `4684714ee133794cdbb86630e42b7d93447fb2e2`
Files changed: `docs/research/holaos-capability-ledger.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: reuse eligible non-visual runtime/client/SDK implementation behind adapters; exclude shared UI and branded desktop frontend; keep holaOS memory transient and Semantica authoritative
Assumptions: README capability descriptions require source-level and runtime validation before integration claims
Blocked items: no local pinned checkout/build; exact file-level MCP/provider/browser/integration/automation paths remain a later acquisition/compatibility gate
Next exact action: commit/push P1-T03, then claim P1-T04
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; this verified unit is ready to commit and push

## 2026-08-31 - P1-T03 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `64bb3a9`
Scope: map holaOS capabilities, source entry points, non-visual reuse candidates, visual/branding exclusions, and distribution obligations
Files intended: `docs/research/holaos-capability-ledger.md`, master tracker, and handoff
Actions: claimed P1-T03 in plan order
Verification: pending official source tree/package/license inspection and ledger completeness scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: maximize licensed non-visual reuse during personal non-commercial development while maintaining a separable public-distribution boundary
Assumptions: exact main commit must be recorded because `latest` is rolling
Blocked items: none
Next exact action: inspect official repository metadata, current main commit, package/workspace manifests, source tree, README, and LICENSE
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T02 - exit

Executor: Codex root agent
Starting git state: clean after `b799a63`
Scope: refresh Semantica v0.6.7 version, API, capability, packaging, storage, and reuse-boundary evidence
Files intended: upstream matrix, master tracker, and handoff
Actions: verified official v0.6.7 tag target, release assets/digests, Python manifest, entry points, dependency shape, AgentContext surface, and current Forma AI integration boundary
Verification: expected repository `rg` scan passed; matrix contains exact commit, asset digests, five entry points, upstream capability table, and product responsibility boundary; whitespace check passed
Evidence: official Semantica GitHub tag/release API, versioned `pyproject.toml`, pinned `AgentContext` source, Forma AI adapter/backend/runbook and ADR-0011
Files changed: `docs/research/upstream-matrix.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: directly reuse AgentContext and upstream decision/causal/provenance/graph/MCP capabilities; product-owned code remains governance, isolation, approval, audit, and UI integration only
Assumptions: unsigned tag and mutable release metadata require commit plus asset-digest binding
Blocked items: real managed Semantica runtime and production embedding approval remain later implementation gates, not blockers for inventory
Next exact action: commit/push P1-T02, then claim P1-T03
Approval needed: none
Secret/external-write status: no secrets; official public sources only
Quota state and closeout action: normal; independently verified unit ready to commit and push

## 2026-08-31 - P1-T02 - takeover

Executor: Codex root agent
Starting git state: clean after pushed commit `b799a63`
Scope: refresh Semantica v0.6.7 API, capability, packaging, storage, and reuse-boundary evidence
Files intended: `docs/research/upstream-matrix.md`, master tracker, and handoff
Actions: claimed P1-T02 in plan order
Verification: pending official repository/tag/package inspection and repository boundary scan
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: Semantica remains the governed memory authority; reuse upstream APIs/packages rather than reconstructing memory primitives
Assumptions: versioned v0.6.7 evidence controls the current pin even if `main` has moved
Blocked items: none
Next exact action: inspect official v0.6.7 release, manifest, CLI/MCP/server/storage surfaces, and compare with Forma AI adapters
Approval needed: none
Secret/external-write status: no secrets; public read-only source access only
Quota state and closeout action: normal; close and push this documentation unit on warning

## 2026-08-31 - P1-T01 - exit

Executor: Codex root agent
Starting git state: clean at `5cee7a9`
Scope: inventory repository and bounded machine-local checkouts, pins, and installed artifacts for all four upstream foundations
Files intended: upstream matrix, master tracker, and handoff
Actions: scanned repository integrations, prior research workspace, normal Applications folders, and product-managed support paths; inspected the oMLX bundle and active artifact record; distinguished empty research directories from Git checkouts
Verification: repository file scan found Semantica/oMLX adapters only; no upstream Git checkout was found in the bounded search; Semantica-named research directory is not a Git repository; installed oMLX reports bundle ID `app.omlx`, version `0.6.3`, build `2500`, and the expected artifact digest
Evidence: updated `docs/research/upstream-matrix.md` local inventory table; `config/upstreams.json`; `config/product-manifest.json`; read-only oMLX Info.plist and active record
Files changed: `docs/research/upstream-matrix.md`, master tracker, and this handoff
Commit: pending documentation commit
Push: pending
Decisions: installed oMLX is binary evidence, not source evidence; `latest` is not an acceptable holaOS pin; absence of local source never authorizes reimplementation
Assumptions: search is explicitly bounded and does not prove machine-wide absence
Blocked items: none for P1-T01
Next exact action: commit/push P1-T01, then claim P1-T02
Approval needed: none
Secret/external-write status: no secrets; no cloud calls
Quota state and closeout action: normal; task is independently committable and ready for quota-safe closeout

## 2026-08-31 - P1-T01 - takeover

Executor: Codex root agent
Starting git state: clean at `5cee7a9`; legacy build artifacts preserved in `stash@{0}`
Scope: list available local upstream checkouts, installed artifacts, declared pins, and gaps for all four foundations
Files intended: `docs/research/upstream-matrix.md`, master tracker, and this handoff
Actions: claimed P1-T01 after confirming the previous quota-safe closeout and reviewing the execution plan
Verification: pending repository file inventory and read-only local source discovery
Evidence: pending
Files changed: tracker and handoff at takeover
Commit: none yet
Push: none yet
Decisions: inventory only; no upstream modification or new capability implementation
Assumptions: local checkouts outside the repository are read-only evidence and are not product dependencies until pinned and integrated
Blocked items: none
Next exact action: scan repository references, known development directories, installed application locations, and Git metadata for exact pins
Approval needed: none for read-only discovery
Secret/external-write status: no secrets; no cloud calls
Quota state and closeout action: normal; close current task immediately if a usage warning appears

## 2026-08-31 05:57 Asia/Shanghai - P0-T08 - exit

Executor: Codex root agent
Starting git state: quota-interrupted P0-T08 worktree plus preserved earlier DeepSeek/settings edits
Scope: resume at the exact interruption point, finish Forma AI global rename, icon contract test, validation, and quota-safe closeout
Files intended: all tracked product identity surfaces, Python module/import names, Swift targets, packaging identifiers, documentation, tests, and Forma AI icon assets
Actions: added missing automated icon assertions; confirmed product name/module/target/executable/environment/service/support-path migration; generated standard iconset and ICNS; integrated icon in Info.plist and app build; added the Codex quota exhaustion protocol
Verification: legacy-name scan outside preserved untracked historical build returned no match; full Python suite passed 225 with 1 skipped; targeted packaging suite passed 6; Swift suite passed 30 with 2 skipped; temporary signed `Forma AI.app` built successfully; Info.plist exposes `CFBundleName=Forma AI` and `CFBundleIconFile=FormaAI`; ICNS identified as a macOS icon; codesign verification passed; `git diff --check` passed
Evidence: `assets/branding/forma-ai-app-icon-1024.png`, `prototypes/packaging/Resources/FormaAI.icns`, temporary validation bundle `/tmp/forma-ai-validation-20260831-0203/Forma AI.app`
Files changed: tracked product source/tests/docs/config/packaging naming plus new branding and icon resources; earlier DeepSeek/settings edits are locally test-verified but the real DeepSeek closed loop remains pending under P5
Commit: `7068cba feat: rename product to Forma AI`; closeout commit `43ba7b1 docs: close Forma AI identity migration`
Push: commits through `43ba7b1` pushed to `origin/main`; final status record follows as documentation-only commit
Decisions: product and internal identity are Forma AI; no split legacy module/target/service identity remains in tracked files; generated build artifacts are not product source
Assumptions: pre-existing local DeepSeek/settings edits can be included because full Python and Swift suites pass, without claiming P5 real-provider acceptance
Blocked items: no P0-T08 blocker; real DeepSeek acceptance remains explicitly open
Next exact action: claim P1-T01 and inventory the four upstream checkouts/pins before new capability implementation
Approval needed: separate explicit approval remains required for a real DeepSeek call
Secret/external-write status: no project credential read or transmitted; only repository push remains
Quota state and closeout action: resumed after quota reset; completed and pushed the smallest verified unit; repository is clean; pre-existing untracked artifacts are preserved in `stash@{0}` named `pre-Forma legacy build artifacts and generated iconset 2026-08-31`

## 2026-08-31 - P0-T08 - takeover

Executor: Codex root agent
Starting git state: P0-T07 committed; earlier DeepSeek/settings source changes remain dirty and must be preserved through the mechanical rename
Scope: rename the product globally to Forma AI and add an original macOS application icon
Files intended: tracked source, tests, documentation, Swift package/targets, build scripts, product manifest, application metadata, and new icon assets
Actions: generated an original 1024px macOS icon concept using the built-in image generation workflow; inventoried tracked legacy names and identifiers
Verification: pending legacy-name absence scan, Python suite, Swift suite, and application bundle inspection
Evidence: generated source image at the Codex generated-image path; final project asset pending copy and iconset creation
Files changed: master tracker and handoff at takeover
Commit: P0-T07 commits `a618993` and `d190d90` complete; P0-T08 pending
Push: pending combined push
Decisions: public product name is `Forma AI`; internal module, target, executable, environment, support-directory, service, bundle, and documentation names will be migrated rather than leaving a split identity
Assumptions: historical evidence wording may be updated for product identity, while technical results and dates remain unchanged
Blocked items: none
Next exact action: perform mechanical rename, preserve dirty functional edits, create icon assets, update package metadata, and test
Approval needed: none for repository-local rename and generated asset integration
Secret/external-write status: no secrets handled; image generation only, no cloud model credential used from the project

## 2026-08-31 01:57 Asia/Shanghai - P0-T07 - exit

Executor: Codex root agent
Starting git state: dirty worktree with previously recorded DeepSeek/settings implementation changes
Scope: reconcile product-role documents and make upstream-first reuse enforceable
Files intended: governance, requirements, decisions, ADR-0017, active/legacy plans, license matrix, tracker, and handoff
Actions: corrected active role conflicts; marked the old plan superseded; made Herdr core; required licensed non-visual reuse from all four upstreams; separated personal non-commercial development from future public distribution; added universal Codex/Claude-compatible agent adapters and complete product Settings to requirements and the master plan
Verification: repository-wide role scan found no unmarked active conflict; `git diff --check` passed for all documentation files
Evidence: upstream-first implementation rule in `AGENTS.md`; ADR-003 superseded by ADR-017; ADR-0017 and product requirements require Herdr and upstream reuse; master plan contains CAP-11, CAP-12, P2-T07, and P4-T07
Files changed: `AGENTS.md`, `docs/decisions.md`, `docs/product-requirements.md`, `docs/adr/0017-product-owned-native-workbench.md`, both 2026-08-28 plans, license matrix, master tracker, and this handoff
Commit: `a618993 docs: enforce upstream-first product direction`; this closeout record follows in a documentation-only commit
Push: pending final closeout push
Decisions: independent visual workbench plus adapter protocol; reuse all license-permitted non-visual upstream capability; do not duplicate upstream functionality without recorded justification
Assumptions: personal non-commercial use does not waive license obligations; future public distribution requires a fresh exact-artifact review
Blocked items: none
Next exact action: commit and push documentation only, then claim P1-T01
Approval needed: none for documentation; cloud calls remain separately approval-gated
Secret/external-write status: no secrets handled; no cloud API calls

## 2026-08-31 - P0-T07 - takeover

Executor: Codex root agent
Starting git state: dirty worktree with the previously recorded DeepSeek/settings implementation changes
Scope: align active and legacy product documents with the confirmed independent-workbench, adapter-protocol, and upstream-first reuse target
Files intended: `AGENTS.md`, product requirements, decisions, ADR-0017, active/legacy plans, license matrix, master tracker, and this handoff
Actions: claimed P0-T07 after repository-wide conflict scan found documents that still called holaOS the default UI and Herdr optional
Verification: pending repository-wide role/reuse conflict scan and whitespace validation
Evidence: conflicts found in `docs/decisions.md`, `docs/product-requirements.md`, `docs/adr/0017-product-owned-native-workbench.md`, and `docs/plans/2026-08-28-forma-ai.md`
Files changed: master tracker and this handoff at takeover
Commit: none yet
Push: none yet
Decisions: reuse existing upstream functionality before product-owned implementation; new implementation is limited to the independent workbench, adapter/protocol/integration/policy gaps, license-blocked portions, or verified upstream capability gaps
Assumptions: non-commercial personal development does not waive license terms; public distribution remains a separate release gate
Blocked items: none
Next exact action: update conflicting documents, scan, verify, commit documentation only, and push
Approval needed: none for repository documentation edits
Secret/external-write status: no secrets handled; no cloud API calls

## 2026-08-31 - P0-T01 - takeover

Executor: Codex root agent
Starting git state: dirty worktree with DeepSeek/settings/test/build changes listed above
Scope: create execution-control documents and update `AGENTS.md`
Files intended: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`, `AGENTS.md`
Actions: started governance correction after user confirmed the need for granular tracking and handoff
Verification: `rg -n "Execution control documents|Task Handoff|Current Baton|P0-T01|Herdr is the core|holaOS is a capability"` found required anchors; `git diff --check -- AGENTS.md docs/plans/2026-08-31-multi-agent-workbench-master-plan.md docs/TASK_HANDOFF.md` passed
Evidence: `AGENTS.md` contains mandatory execution-control rules; master plan contains P0-P8 tracker; this file contains takeover protocol and current dirty-worktree baton
Files changed: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: `3756677 docs: add workbench execution control`
Push: governance documentation chain is pushed together with this final completion update
Decisions: product-owned independent workbench plus adapter protocol; holaOS capability parity without uncleared public bundling; Herdr core multi-agent runtime
Assumptions: documentation-control commit must not stage the interrupted implementation files
Blocked items: none for documentation-control task
Next exact action: claim P1-T01 or explicitly resume P5 DeepSeek work if the user chooses that path
Approval needed: none for documentation edits; separate approval still required for any cloud API call
Secret/external-write status: no secrets handled; no external cloud calls in this task

## 2026-08-31 - P0-T05 - exit

Executor: Codex root agent
Starting git state: dirty worktree with prior DeepSeek/settings changes preserved
Scope: commit governance documents only
Files intended: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Actions: staged only governance documents and committed them
Verification: `git diff --cached --name-only` listed only the three intended files before commit
Evidence: commit `3756677 docs: add workbench execution control`
Files changed: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: `3756677`
Push: pending
Decisions: completion evidence must be written back before push closeout
Assumptions: second documentation commit is acceptable to avoid self-referential commit metadata
Blocked items: none
Next exact action: commit this completion-record update, push, then mark P0-T06 verified
Approval needed: none
Secret/external-write status: no secrets handled; no external cloud calls

## 2026-08-31 - P0-T06 - exit

Executor: Codex root agent
Starting git state: dirty worktree with prior DeepSeek/settings changes preserved
Scope: push governance documentation chain
Files intended: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Actions: marked P0 governance correction verified and set next task to P1-T01
Verification: documentation anchors and whitespace checks passed before commits; staged file checks excluded implementation work
Evidence: commits `3756677` and `7b516a1`, plus this final completion update, form the governance documentation chain
Files changed: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: this completion update is committed after editing
Push: pushed with governance documentation chain
Decisions: next default task is P1-T01; DeepSeek real closed loop remains P5 unless the user explicitly reprioritizes it
Assumptions: no cloud calls are authorized by this documentation-control task
Blocked items: none
Next exact action: begin P1-T01 or explicitly resume P5-T01/P5-T04
Approval needed: DeepSeek real-provider calls still need explicit per-run approval and test credential confirmation
Secret/external-write status: no secrets handled; no external cloud calls
