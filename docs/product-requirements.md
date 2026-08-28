# Mac AI Work OS Product Requirements

Status: product baseline draft, 2026-08-28.

## 1. Objective

Deliver a general-purpose Mac application that turns Semantica, holaOS, Herdr, and oMLX into one coherent AI work operating system. A non-expert must be able to install it, complete guided setup, run useful tasks, approve real-world actions, inspect what happened, recover from failures, update it, and remove it without learning the underlying protocols.

The current developer Mac is a test environment. Personal files, MyNote, GBrain, private accounts, and existing workflows are not product dependencies.

## 2. Target users

- **Ordinary knowledge worker:** uses the unified graphical experience and recommended safe defaults.
- **Power user:** connects applications, reviews audit and memory, and changes models or retention without editing code.
- **Developer/operator:** uses Herdr, diagnostics, APIs, logs, and component overrides without adding complexity to the primary path.

## 3. Core journeys

1. Download one trusted artifact, complete compatibility checks and guided setup, then run a verified sample task.
2. Save a sourced fact or decision, inspect provenance, correct it, export it, and delete it.
3. Run parallel agents, see status and approvals, cancel work, and receive one validated result.
4. Connect a real tool, preview scope, approve one action, verify its outcome, audit it, and revoke access.
5. Diagnose a failed component, retry safely, recover state, or deliberately select an explained degraded mode.
6. Upgrade without losing governed data, roll back failure, and uninstall with keep/export/delete choices.

## 4. Functional requirements

### FR-1 Unified lifecycle

One supported installer owns prerequisites, version pins, first-run setup, start, stop, restart, update, rollback, and uninstall. Users do not install packages, edit JSON, manage ports, or start four services manually. Installation is resumable and partial state is repairable.

### FR-2 Hardware-aware setup

Detect chip, macOS, memory, disk, and port conflicts; map supported Macs to tested profiles; explain model recommendations; refuse unsupported combinations before large downloads or changes.

### FR-3 Unified interaction

holaOS is the default experience. Tasks, approvals, status, results, memory review, and recovery work without a terminal. Herdr is optional progressive disclosure.

### FR-4 Governed memory

Separate raw inputs, audit records, candidate knowledge, and confirmed knowledge. Confirmed records carry provenance, timestamps, status, version, and correction/deletion history. Semantica is the authority; transient UI memory is not a competing truth source.

### FR-5 End-to-end audit

Every material run has a correlation ID linking request, agent, model, retrieval, tools, approvals, mutations, validation, failures, result, and memory changes. Audit distinguishes denied, failed, partial, rolled-back, and completed actions and supports redaction and retention.

### FR-6 Parallel agents

Run, observe, pause, approve, cancel, and recover multiple agents. Aggregate results only after validation. Reconnect without falsely marking work complete.

### FR-7 Local-first inference

oMLX is the default service on supported Apple Silicon. Model capability, resource use, privacy route, and fallback are visible. Silent cloud fallback is prohibited.

### FR-8 Real tools and permissions

Connectors declare read, write, send, delete, execute, and credential scopes separately. Material actions provide preview, scoped approval, verification, revocation, and audit. Denial and timeout are first-class outcomes.

### FR-9 Honest health and recovery

Report component health and workflow health separately. Missing capability cannot appear as an empty success. Backup, repair, migration, restart, and rollback are tested.

### FR-10 Extensibility

Versioned contracts isolate UI, policy, orchestration, inference, memory, agents, and connectors. The four projects are the default distribution rather than hard-coded business assumptions.

## 5. Quality requirements

- A first-time non-developer completes recommended setup without terminal commands.
- On supported hardware, verified sample-task time is under 20 minutes excluding separately displayed model download time.
- Every blocker states cause, affected capability, safe next action, and data risk.
- Secrets use macOS-appropriate secure storage and never enter Git, logs, or diagnostic exports.
- Lifecycle operations are idempotent or have deterministic repair.
- Primary flows are keyboard accessible with meaningful labels and status.
- Performance claims are measured per supported hardware tier.
- Upstream versions, licenses, and replaceability are documented.

## 6. Distribution scope

The first release targets Apple Silicon Macs. Exact minimum macOS, RAM, disk, and model tiers must come from live tests. Publish minimum/recommended profiles, storage/download footprint, limitations, versions, and licenses. Intel Mac support is out of scope until designed and tested.

## 7. Release acceptance

A release requires evidence for:

1. clean and interrupted install, recovery, restart, upgrade, rollback, and uninstall;
2. hardware detection and correct profile recommendation;
3. all four component and adapter contracts;
4. memory provenance, conflict, correction, export, retention, and deletion;
5. parallel work, approval wait, cancellation, reconnect, and validation;
6. a real connector read and reversible scoped write with preview, approval, verification, and audit;
7. per-component failure injection without silent fallback;
8. security, privacy, accessibility, and usability reviews;
9. one user unfamiliar with implementation completing installation and core journeys from public documentation without hidden help.

## 8. Pending decisions

- Product name and application identity.
- Packaging: native app with managed services, signed package/launcher, or another tested option.
- Redistribution and license rights for each upstream component.
- Supported hardware/model tiers.
- Whether cloud inference is absent or a separately enabled provider.
- First reversible connector for end-to-end acceptance.
