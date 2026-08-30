# Mac AI Work OS Task Handoff

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

## Current Baton

Updated: 2026-08-31 Asia/Shanghai
Owner: Codex root agent
Master plan task: P0-T05
State: documentation-control files created and validated; committing docs only
Next required action: commit only documentation-control changes, push, then update this handoff with the commit result.

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

- `mac_ai_work_os/deepseek_adapter.py`
- `tests/test_deepseek_adapter.py`
- `prototypes/packaging/Sources/LifecycleContract/ProductManifest.swift`
- `prototypes/packaging/Sources/MacAIWorkOSApp/MacAIWorkOSApp.swift`
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
```

## Handoff Log

## 2026-08-31 - P0-T01 - takeover

Executor: Codex root agent
Starting git state: dirty worktree with DeepSeek/settings/test/build changes listed above
Scope: create execution-control documents and update `AGENTS.md`
Files intended: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`, `AGENTS.md`
Actions: started governance correction after user confirmed the need for granular tracking and handoff
Verification: `rg -n "Execution control documents|Task Handoff|Current Baton|P0-T01|Herdr is the core|holaOS is a capability"` found required anchors; `git diff --check -- AGENTS.md docs/plans/2026-08-31-multi-agent-workbench-master-plan.md docs/TASK_HANDOFF.md` passed
Evidence: `AGENTS.md` contains mandatory execution-control rules; master plan contains P0-P8 tracker; this file contains takeover protocol and current dirty-worktree baton
Files changed: `AGENTS.md`, `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`, `docs/TASK_HANDOFF.md`
Commit: pending
Push: pending
Decisions: product-owned independent workbench plus adapter protocol; holaOS capability parity without uncleared public bundling; Herdr core multi-agent runtime
Assumptions: documentation-control commit must not stage the interrupted implementation files
Blocked items: none for documentation-control task
Next exact action: update `AGENTS.md`, run documentation validation, commit and push docs only
Approval needed: none for documentation edits; separate approval still required for any cloud API call
Secret/external-write status: no secrets handled; no external cloud calls in this task
