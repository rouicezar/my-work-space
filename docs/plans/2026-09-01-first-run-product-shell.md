# First Run and Product Shell Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the complete final product shape understandable from first launch through daily task creation and transition into the multi-agent execution thread.

**Architecture:** Add product-owned read-only presentation contracts and DEBUG-only preview surfaces before runtime binding. The novice flow uses product language only; upstream component identities remain hidden outside advanced diagnostics. Production initialization remains runtime-first and never falls back to synthetic preview.

**Tech Stack:** Swift 6.2, SwiftUI for macOS, Swift Testing, existing LifecycleContract and ProductPreviewProvider targets.

---

### Task 1: P4-T12A First-Run Assistant

**Files:**
- Modify: `prototypes/packaging/Sources/LifecycleContract/ProductPreviewProvider.swift`
- Create: `prototypes/packaging/Sources/FormaAIApp/FirstRunPreview.swift`
- Modify: `prototypes/packaging/Sources/FormaAIApp/FormaAIApp.swift`
- Modify: `prototypes/packaging/Tests/LifecycleContractTests/ProductPreviewProviderTests.swift`

**Steps:**
1. Add a failing contract test for welcome, privacy, automatic local-AI preparation, recommended local model, macOS permissions, optional cloud, and create-first-task steps.
2. Run the filtered Swift test and confirm the first-run contract is missing.
3. Add immutable product-language contracts with no required upstream-project names or manual-terminal step.
4. Render a DEBUG-only `--first-run-preview` assistant with persistent Preview disclosure and inert navigation.
5. Run filtered/full Swift tests, forbidden-word/action scans, window-only screenshot review, and `git diff --check`.
6. Synchronize bilingual controls, commit, and push.

### Task 2: P4-T12B Daily Product Shell

**Files:**
- Create: `prototypes/packaging/Sources/FormaAIApp/DailyWorkbenchPreview.swift`
- Modify: lifecycle presentation contracts and tests

**Steps:**
1. Add a failing contract for sidebar navigation, recent tasks, central New Task composer, route/privacy summary, context attachments, and collapsible supervision rail.
2. Implement the read-only DEBUG preview with no fake history or runtime actions.
3. Verify tests, source boundaries, resizing, and window-only screenshot evidence.
4. Synchronize, commit, and push.

### Task 3: P4-T12C New Task to Execution Transition

**Files:**
- Modify: Product Preview presentation models and SwiftUI preview surfaces
- Modify: lifecycle tests

**Steps:**
1. Add a failing deterministic transition contract for compose, route review, plan, parallel execution, approval, validation, and result.
2. Implement only ephemeral Preview navigation between deterministic states; never submit a task.
3. Verify production default, no command calls, tests, and normal-speed manual walkthrough.
4. Synchronize, commit, and push; return baton to P4-T13.
