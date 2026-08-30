# Forma AI Product Design

Status: product architecture baseline draft.

## Product shape

Use a product-owned native shell and versioned adapter protocol around four upstream foundations. The native workbench is the default experience and owns the unified interaction, policy, lifecycle, and audit contract. Licensed non-visual capabilities from Semantica, holaOS, Herdr, and oMLX are reused before product-owned equivalents are considered. holaOS visual assets and public bundling remain separately gated by license and branding terms.

```text
Forma AI
├── Installer and First-Run Assistant
├── Product-owned Native Workbench
├── Policy and Approval Service
├── Orchestrator and Audit Correlator
├── Lifecycle and Health Supervisor
├── Component Adapters
│   ├── Semantica — governed memory and decision evidence
│   ├── holaOS — reusable workflow and application capabilities
│   ├── Herdr — core multi-agent execution runtime
│   └── oMLX — local inference
├── Inference Router
│   ├── Local Qwen route — default
│   └── Cloud Provider Adapter — DeepSeek initially, disabled by default
└── Connector and Extension Contracts
```

This avoids a loose bundle that exposes four installations and failure models and avoids rebuilding functionality already maintained upstream. Thin tested adapters plus a product lifecycle layer preserve reuse, replaceability, and coherence. New product-owned capability requires a documented upstream search and a license, compatibility, security, maintainability, or verified capability-gap reason.

## User modes

Standard mode presents tasks, approvals, results, memory, connectors, and simple health in a restrained conversation-centered native workbench inspired by proven AI coding workspaces. Advanced mode adds model profiles, retention, audit, and agent status. Developer mode exposes the holaOS integration surface, Herdr console, logs, APIs, and adapter diagnostics. Users move upward deliberately; primary setup never requires advanced layers.

## Task and data flow

Every task receives a correlation ID and risk classification. Policy determines allowed tools, data routes, approval, and retention. The orchestrator retrieves only governed Semantica knowledge, selects a visible model route, reuses holaOS workflow/application capabilities where applicable, and executes agent work through Herdr. Tool mutations are previewed and approved. Validation precedes completion. Audit links all phases. Candidate memory is promoted only after provenance, conflict, and policy gates.

Inference routing is a product policy decision, not an opaque model choice. A task
contract declares required input types, approximate context, tool schemas, quality
validator, latency class, and privacy classes. If local health and the tested Qwen
profile satisfy that contract, the request stays local. If the task is ineligible or
the local result fails its declared validator, the router may create a DeepSeek
escalation proposal; it may not transmit anything yet.

The proposal contains the reason, exact post-redaction payload manifest and digest,
provider/model, current catalog provenance, estimated input/output range and cost,
data classes, side effects, and cancellation behavior. A one-shot approval token binds
those fields. The cloud adapter re-hashes the serialized outbound body immediately
before transmission and refuses mismatches. Cloud-produced tool calls are proposals
only and re-enter the normal tool permission gate. Provider failure returns to the
user as failure or a new explicit choice, never a hidden route change.

The provider adapter contract separates model discovery, health, request planning,
transmission, response normalization, usage accounting, cancellation, and error
classification. DeepSeek uses its current OpenAI-compatible HTTPS API behind this
contract; model names and pricing remain catalog data rather than application code.
The API key is read from Keychain only for the outbound call and never passed in
arguments, files, UI state, audit events, or diagnostic bundles.

Raw content, audit, candidates, confirmed knowledge, secrets, configuration, and user artifacts use separate storage classes.

## Lifecycle

A trusted artifact installs the app and a version-pinned component manifest. A supervisor owns downloads, verification, configuration, ports, start order, health, migrations, backup, update, rollback, and uninstall. First run detects hardware, selects a tested profile, estimates downloads, obtains consent, and executes a sample workflow.

Installation is a recoverable state machine, not a one-shot script. User data is versioned separately from binaries so upgrade and uninstall can preserve, export, or delete it explicitly.

## Safety and honest degradation

Read, write, send, delete, execute, credential use, and external transmission are separate capabilities. Material actions show target, mutation, side effects, and reversibility. Approval tokens are narrow, expiring, task-bound, and audited. Secrets use secure storage.

No failure silently changes semantics: missing Semantica disables memory-backed
claims; missing or insufficient oMLX can only produce a visible cloud proposal;
missing DeepSeek configuration, denied approval, stale cost data, or provider failure
cannot masquerade as a local result; missing Herdr disables background continuity;
connector uncertainty is unknown/failed rather than empty success.

## Packaging and licensing gate

Before packaging, verify current APIs, system requirements, data locations, update behavior, redistribution terms, trademarks, bundled assets, and transitive licenses. A component may need first-run download rather than bundling. Technical compatibility is not legal permission to distribute.

## Verification

Contract, lifecycle, synthetic workflow, reversible real-connector, failure injection, security, hardware benchmark, visual/accessibility, and novice-user tests form separate gates. A requirement-to-evidence index prevents narrow health checks from standing in for product usability.
