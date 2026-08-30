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
Master plan task: P1-T01
State: Forma AI rename and icon integration committed; pending closeout push and clean-status confirmation
Next required action: commit this closeout record, preserve untracked legacy artifacts in a named stash, push, confirm clean repository, then claim P1-T01 for the four-upstream inventory.

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

## 2026-08-31 05:57 Asia/Shanghai - P0-T08 - exit

Executor: Codex root agent
Starting git state: quota-interrupted P0-T08 worktree plus preserved earlier DeepSeek/settings edits
Scope: resume at the exact interruption point, finish Forma AI global rename, icon contract test, validation, and quota-safe closeout
Files intended: all tracked product identity surfaces, Python module/import names, Swift targets, packaging identifiers, documentation, tests, and Forma AI icon assets
Actions: added missing automated icon assertions; confirmed product name/module/target/executable/environment/service/support-path migration; generated standard iconset and ICNS; integrated icon in Info.plist and app build; added the Codex quota exhaustion protocol
Verification: legacy-name scan outside preserved untracked historical build returned no match; full Python suite passed 225 with 1 skipped; targeted packaging suite passed 6; Swift suite passed 30 with 2 skipped; temporary signed `Forma AI.app` built successfully; Info.plist exposes `CFBundleName=Forma AI` and `CFBundleIconFile=FormaAI`; ICNS identified as a macOS icon; codesign verification passed; `git diff --check` passed
Evidence: `assets/branding/forma-ai-app-icon-1024.png`, `prototypes/packaging/Resources/FormaAI.icns`, temporary validation bundle `/tmp/forma-ai-validation-20260831-0203/Forma AI.app`
Files changed: tracked product source/tests/docs/config/packaging naming plus new branding and icon resources; earlier DeepSeek/settings edits are locally test-verified but the real DeepSeek closed loop remains pending under P5
Commit: `7068cba feat: rename product to Forma AI`; this exit metadata follows in a documentation-only closeout commit
Push: pending final closeout push
Decisions: product and internal identity are Forma AI; no split legacy module/target/service identity remains in tracked files; generated build artifacts are not product source
Assumptions: pre-existing local DeepSeek/settings edits can be included because full Python and Swift suites pass, without claiming P5 real-provider acceptance
Blocked items: no P0-T08 blocker; real DeepSeek acceptance remains explicitly open
Next exact action: stage tracked changes and formal icon assets only, commit, stash preserved untracked legacy artifacts, push, confirm clean status, then start P1-T01
Approval needed: separate explicit approval remains required for a real DeepSeek call
Secret/external-write status: no project credential read or transmitted; only repository push remains
Quota state and closeout action: resumed after quota reset; following the new protocol by completing the smallest verified unit, committing, pushing, and leaving a clean recoverable state

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
