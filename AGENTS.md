# Project Agent Instructions

## Product scope

Build a general-purpose, distributable, out-of-the-box Forma AI based on Semantica, holaOS, Herdr, and oMLX. The current machine is the first development environment, not the product's sole target or a source of product-specific assumptions.

The product is a local-first, multi-agent Mac AI workbench. Its default distributable shape is a product-owned native workbench plus adapter protocol. It must let a local small model coordinate work, route tasks, use memory, and supervise parallel agents while also allowing explicit, approved cloud-model execution when configured.

Do not let the project drift into a setup-only utility, a model downloader, a single-chat demo, or a thin wrapper around one upstream project.

## Upstream-first implementation rule

Semantica, holaOS, Herdr, and oMLX are the functional foundation of the product. Reuse their existing non-visual capabilities as far as their licenses and verified APIs permit. The product-owned implementation is limited to the independent workbench UI, adapter protocol, integration/orchestration/policy/lifecycle layers, license-blocked portions, and capabilities proven absent upstream.

Before implementing any capability that may already exist in one of the four upstream projects, the executing agent must record the upstream search result, reusable entry point, license obligation, and integration decision in the master plan evidence or the relevant capability ledger. If an upstream implementation exists and its license permits the intended use, duplicating it is a drift stop condition. Personal, non-commercial development does not waive license terms; future public distribution has a separate release-time license, notice, asset, and trademark gate.

## Execution control documents

The project has two required control documents:

- Master execution plan and progress tracker: `docs/plans/2026-08-31-multi-agent-workbench-master-plan.md`
- Task takeover and recovery handoff: `docs/TASK_HANDOFF.md`

Before changing product code or product documentation, every agent must:

1. Read this file.
2. Read the master execution plan and progress tracker.
3. Read the task handoff document.
4. Inspect the current git status.
5. Claim exactly one task ID by setting it to `in_progress` in the master plan.
6. Add a takeover entry to `docs/TASK_HANDOFF.md`.

Before ending any implementation, documentation, test, commit, or phase task, every agent must:

1. Update the claimed task status in the master plan.
2. Add an exit entry to `docs/TASK_HANDOFF.md`.
3. Record verification evidence, changed files, commit status, push status, blockers, and the next exact action.

No task is complete unless both control documents are updated. Do not create a competing tracker, roadmap, or handoff file unless the user explicitly replaces these paths.

## Codex quota exhaustion protocol

When the Codex usage limit is close to exhaustion, stop starting new work units immediately. Finish only the smallest currently active safe unit, run its required verification, update the master tracker and handoff, commit and push verified changes, and confirm the repository is clean before stopping.

Do not force a clean repository by discarding user or pre-existing agent changes. If unrelated dirty work prevents a clean state, preserve it, identify every path and owner in `docs/TASK_HANDOFF.md`, isolate the verified commit from it, and state the exact recovery action. Unverified partial work must either be safely reverted when it was created solely by the current agent and no useful work would be lost, or left explicitly claimed with a recovery recipe; it must never be hidden in a completion commit.

## Workflow

Follow `requirements → design → implementation → testing → commit → push`.

- Do not implement before requirements and design are accepted.
- Prefer minimal, reversible changes and stable public contracts.
- Test every implementation change and verify the user-visible workflow.
- Keep facts, assumptions, hypotheses, predictions, and opinions distinct.
- Distribution, upgrade, uninstall, documentation, and novice-user evidence are required product work.
- Keep the master execution tracker and task handoff current after every completed task or blocked stop.

## Development isolation

Do not use developer-specific data as a product dependency or modify MyNote, GBrain, existing automations, persistent agent memory, or production accounts without a separately approved connector or migration task. Use repository-local fixtures, test accounts, temporary databases, and synthetic data. Never commit secrets, personal paths in shipped configuration, or machine-specific credentials.

## Component roles

- The product-owned native workbench is the default user-facing control plane for distributable builds.
- holaOS is a capability/workflow reference and optional separately installed adapter until redistribution is cleared. Do not copy, rebadge, or bundle holaOS frontend/source/assets into a public release without explicit license clearance.
- Herdr is the core multi-agent execution runtime. It must support parallel execution, readable state, cancellation, resume, recovery, and handoff.
- Semantica is authoritative for governed long-term knowledge and decision evidence.
- oMLX is the default local inference layer.
- Product-owned orchestration, policy, lifecycle, and health layers integrate them.

## Drift stop conditions

Stop and ask for direction before proceeding if a task would:

- reduce holaOS capability parity because of visual redesign;
- make Herdr optional for the core multi-agent loop;
- create a second long-term memory authority competing with Semantica;
- treat oMLX health as proof of inference without an actual completion or embedding call;
- send data to a cloud model without credential state, preview, explicit approval, and audit;
- copy or ship upstream assets whose redistribution is not cleared;
- reimplement a non-visual capability already available from Semantica, holaOS, Herdr, or oMLX without a documented license, compatibility, security, or capability-gap reason;
- mark a screenshot, failed provider response, or unverified manual observation as acceptance evidence;
- skip updating the master tracker or handoff document.

External writes, destructive actions, credential use, and cloud escalation require explicit policy, preview, approval, and audit behavior. Releases must pass clean-install, upgrade, rollback, uninstall, recovery, security, accessibility/usability, and novice-user gates on supported hardware tiers.
