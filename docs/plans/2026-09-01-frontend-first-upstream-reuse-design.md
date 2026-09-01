# Frontend-First Upstream-Reuse Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Forma AI's final native product shape visible and manually testable early without reimplementing capabilities already owned by Semantica, holaOS, Herdr, or oMLX.

**Architecture:** Build the final SwiftUI information architecture against versioned, read-only presentation contracts derived from verified upstream surfaces. Synthetic preview data is explicit, isolated to preview mode, and never used as runtime evidence. Each visible surface is followed by a vertical integration slice that replaces preview data with the authoritative upstream adapter rather than adding a product-owned runtime.

**Tech Stack:** SwiftUI macOS app, LifecycleContract and SupervisorProtocol Swift packages, product-owned policy/audit envelopes, Herdr socket/CLI, holaOS licensed non-visual interfaces, Semantica managed runtime, oMLX OpenAI-compatible API.

---

## 1. Decision

Forma AI will use a frontend-shape-first sequence, not a frontend-only waterfall.

The user should see and test the intended product early: task workspace, visible parallel agents, approvals, history/recovery, governed memory, agents/tools, and settings. However, a page may not invent execution semantics. Every state and action must map to a named upstream surface or to a narrowly justified product responsibility.

The product preview is a design and usability instrument. It must display a persistent `Preview data · no runtime action` marker, use deterministic repository fixtures, make no network or process calls, write no product state, and ship disabled in release builds unless a later product decision explicitly retains a demo mode.

## 2. Non-duplication authority map

| Capability | Authority | Forma AI responsibility |
|---|---|---|
| Agent processes, panes, state, waits, cancel, reconnect, native resume, worktrees | Herdr | Native presentation, policy checks, correlation, thin protocol translation |
| Workflow/application/tool capabilities available upstream | holaOS | Discover and present capabilities; connect through the thinnest licensed boundary |
| Confirmed long-term knowledge, retrieval, persistence, deletion | Semantica | Candidate/approval/provenance policy only where upstream lacks the product requirement; native review UI |
| Local generation, embedding, reranking, model discovery | oMLX | Safe lifecycle, route policy, approval UI, health and result presentation |
| User intent, native macOS UI, permissions, approvals, cross-component audit, install/update/uninstall | Forma AI | Product-owned implementation |

No task may enter implementation until it records:

1. upstream search result;
2. reusable entry point;
3. license obligation;
4. integration decision;
5. proof that any product-owned code is UI, policy, lifecycle, integration, or a verified gap.

## 3. Frontend product shape

The primary navigation remains deliberately small:

- **New task** — task composition, plan/route summary, live agent activity, approvals, artifacts, result, and validation.
- **History** — durable task list, filters, task detail, interruption/recovery, and audit status.
- **Settings** — General; Models & Providers; Agents & Tools; Memory; Permissions & Approvals; Local Runtime; Data & Privacy; Diagnostics & Recovery.

Approvals, memory review, and agent management are full surfaces inside the relevant task or Settings section rather than additional top-level destinations. This avoids a control-panel-first product while keeping every important function reachable.

The visual direction is a restrained native macOS workbench: clear hierarchy, strong state language, compact operational metadata, accessible keyboard navigation, and no decorative dashboard metrics. The memorable element is the transparent execution thread: user goal → route → agents → approvals → artifacts → verified result.

Every user-visible frontend surface is bilingual and switchable. Simplified Chinese and English copy must come from a shared localization authority rather than page-local string branching. A frontend slice cannot close until both languages have been reviewed in a running window; mixed-language or partially translated states fail acceptance. Preview language changes may remain ephemeral, while release-mode persistence belongs to General settings and onboarding state.

## 4. Preview contract

Create a versioned `ProductPreviewScenario` contract with deterministic scenarios:

- empty/new task;
- local single-agent completion;
- three-agent parallel run with one blocked approval;
- partial result with unresolved evidence;
- cloud proposal before transmission;
- interrupted task eligible for recovery;
- governed-memory candidate/conflict/correction;
- unavailable upstream with an honest recovery action.

Each scenario contains only presentation data: stable synthetic IDs, declared source component, state, summary, timestamps, bounded artifact metadata, and approval preview. It cannot include executors, callbacks, process handles, credentials, or write paths.

## 5. Vertical execution order

### Slice A — Final visible workbench

1. Audit current SwiftUI against the bilingual target guide.
2. Define the presentation contract and preview-only boundary tests.
3. Implement the final task workspace with preview scenarios.
4. Capture and manually review foreground screenshots in light/dark modes and compact/regular sizes.

### Slice B — Real Herdr multi-agent binding

1. Verify the pinned official Herdr artifact, protocol, schema, and socket.
2. Replace preview agent state with `session.snapshot` plus event subscription.
3. Prove two real isolated agent runs, status, wait, graceful cancel, reconnect, and native/fresh resume.
4. Keep preview and runtime providers separate so preview can never satisfy acceptance tests.

### Slice C — holaOS capability binding

1. Audit the pinned workflow/harness/tool surfaces and license boundary.
2. Reuse callable non-visual capabilities through a thin adapter.
3. Present available tools/workflows in Agents & Tools without copying frontend assets or rebuilding upstream logic.

### Slice D — oMLX and approved cloud binding

1. Bind real local model status and completion to the task surface.
2. Preserve one-shot cloud preview/approval/audit.
3. Validate local, proposal, denial, approved cloud, provider error, and no-silent-fallback states.

### Slice E — Semantica memory binding

1. Audit existing product memory code against pinned Semantica.
2. Remove or stop expanding duplicated storage/retrieval behavior.
3. Bind memory review UI to real candidate, confirm, retrieve, correct, export, and delete operations.

### Slice F — History and recovery projection

1. Persist product metadata and correlations only.
2. Reconstruct runtime truth from Herdr snapshot/events and adapter health.
3. Never infer completion or resumability from the local projection alone.

## 6. Error and safety behavior

- Unknown upstream state renders `Unknown` or `Recovery needed`, never `Complete`.
- Preview mode cannot call the Supervisor, adapters, Keychain, network, or filesystem mutation paths.
- Runtime mode cannot fall back to preview data.
- Force termination, external writes, cloud transmission, and credential use remain separate task-bound approvals.
- If an upstream feature is unavailable, the UI shows the missing capability and upstream-derived recovery action; it does not activate a product-owned substitute.

## 7. Testing strategy

- Swift contract tests prove preview/runtime separation and screen reachability.
- Snapshot or semantic UI tests cover every critical state without treating snapshots as runtime evidence.
- Adapter tests use official schema shapes and pinned versions.
- Real integration gates prove at least one end-to-end flow per upstream.
- Manual review covers light/dark appearance, keyboard navigation, text scaling, window resizing, blocked/partial/error states, and normal-speed task flow.
- Release acceptance requires the novice-user script; developer familiarity is not usability evidence.

## 8. Completion definition

Frontend shape is complete when the user can manually traverse and understand every core final-product journey using clearly labeled preview scenarios, with no clipped, unreachable, misleading, or fake-success state.

The product is not complete until those surfaces consume real authoritative upstream state and the full release gates pass. Preview completion and runtime completion remain separate tracker facts.
