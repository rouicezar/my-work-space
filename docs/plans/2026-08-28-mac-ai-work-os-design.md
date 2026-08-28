# Mac AI Work OS Product Design

Status: product architecture baseline draft.

## Product shape

Use a product-owned shell around four replaceable adapters. holaOS remains the default experience, while installation, policy, health, audit correlation, upgrades, and recovery belong to the product rather than four independent lifecycles.

```text
Mac AI Work OS
├── Installer and First-Run Assistant
├── Unified UI (holaOS-based)
├── Policy and Approval Service
├── Orchestrator and Audit Correlator
├── Lifecycle and Health Supervisor
├── Component Adapters
│   ├── Semantica — governed memory and decision evidence
│   ├── holaOS — interaction and application workspace
│   ├── Herdr — advanced agent/process runtime
│   └── oMLX — local inference
└── Connector and Extension Contracts
```

This avoids a loose bundle that exposes four installations and failure models, and a deep fork that creates unsustainable maintenance. Thin tested adapters plus a product lifecycle layer preserve replaceability and coherence.

## User modes

Standard mode presents tasks, approvals, results, memory, connectors, and simple health. Advanced mode adds model profiles, retention, audit, and agent status. Developer mode exposes Herdr, logs, APIs, and adapter diagnostics. Users move upward deliberately; primary setup never requires advanced layers.

## Task and data flow

Every task receives a correlation ID and risk classification. Policy determines allowed tools, data routes, approval, and retention. The orchestrator retrieves only governed Semantica knowledge, selects a visible model route, and runs ordinary work through holaOS. Long or parallel work uses the Herdr adapter. Tool mutations are previewed and approved. Validation precedes completion. Audit links all phases. Candidate memory is promoted only after provenance, conflict, and policy gates.

Raw content, audit, candidates, confirmed knowledge, secrets, configuration, and user artifacts use separate storage classes.

## Lifecycle

A trusted artifact installs the app and a version-pinned component manifest. A supervisor owns downloads, verification, configuration, ports, start order, health, migrations, backup, update, rollback, and uninstall. First run detects hardware, selects a tested profile, estimates downloads, obtains consent, and executes a sample workflow.

Installation is a recoverable state machine, not a one-shot script. User data is versioned separately from binaries so upgrade and uninstall can preserve, export, or delete it explicitly.

## Safety and honest degradation

Read, write, send, delete, execute, credential use, and external transmission are separate capabilities. Material actions show target, mutation, side effects, and reversibility. Approval tokens are narrow, expiring, task-bound, and audited. Secrets use secure storage.

No failure silently changes semantics: missing Semantica disables memory-backed claims; missing oMLX never triggers hidden cloud routing; missing Herdr disables background continuity; connector uncertainty is unknown/failed rather than empty success.

## Packaging and licensing gate

Before packaging, verify current APIs, system requirements, data locations, update behavior, redistribution terms, trademarks, bundled assets, and transitive licenses. A component may need first-run download rather than bundling. Technical compatibility is not legal permission to distribute.

## Verification

Contract, lifecycle, synthetic workflow, reversible real-connector, failure injection, security, hardware benchmark, visual/accessibility, and novice-user tests form separate gates. A requirement-to-evidence index prevents narrow health checks from standing in for product usability.
