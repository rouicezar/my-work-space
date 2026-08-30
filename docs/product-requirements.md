# Mac AI Work OS Product Requirements

Status: product baseline draft, 2026-08-28.

## 1. Objective

Deliver a general-purpose Mac application that turns Semantica, holaOS, Herdr, and oMLX into one coherent AI work operating system. A product-owned native workbench is the default user experience; holaOS remains a replaceable interaction adapter and must not become a distribution dependency until its license and integration contract are approved. A non-expert must be able to install it, complete guided setup, run useful tasks, approve real-world actions, inspect what happened, recover from failures, update it, and remove it without learning the underlying protocols.

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
7. Run a task locally by default; when the verified local capability boundary is exceeded,
   inspect an exact cloud-transmission and cost preview, approve or deny it, and audit the
   resulting DeepSeek request without silent fallback.

## 4. Functional requirements

### FR-1 Unified lifecycle

One supported installer owns prerequisites, version pins, first-run setup, start, stop, restart, update, rollback, and uninstall. Users do not install packages, edit JSON, manage ports, or start four services manually. Installation is resumable and partial state is repairable.

### FR-2 Hardware-aware setup

Detect chip, macOS, memory, disk, and port conflicts; map supported Macs to tested profiles; explain model recommendations; refuse unsupported combinations before large downloads or changes.

### FR-3 Unified interaction

The product-owned native workbench is the default experience. Tasks, approvals, status, results, memory review, and recovery work without a terminal. holaOS and Herdr are optional progressive-disclosure adapters rather than competing primary shells.

The guided setup/repair assistant and the daily workbench are distinct product modes.
After setup is healthy, ordinary launch opens the workbench; installation manifests,
component versions, ports, and adapter diagnostics remain behind Settings or Recovery
instead of occupying the primary task surface.

### FR-4 Governed memory

Separate raw inputs, audit records, candidate knowledge, and confirmed knowledge. Confirmed records carry provenance, timestamps, status, version, and correction/deletion history. Semantica is the authority; transient UI memory is not a competing truth source.

### FR-5 End-to-end audit

Every material run has a correlation ID linking request, agent, model, retrieval, tools, approvals, mutations, validation, failures, result, and memory changes. Audit distinguishes denied, failed, partial, rolled-back, and completed actions and supports redaction and retention.

### FR-6 Parallel agents

Run, observe, pause, approve, cancel, and recover multiple agents. Aggregate results only after validation. Reconnect without falsely marking work complete.

### FR-7 Local-first inference

oMLX with the selected local Qwen model is the default route on supported Apple
Silicon. A product-owned router evaluates declared task requirements, local health,
resource limits, context size, required modalities/tools, and output-validation policy.
It must not infer local incapability solely from a model's self-assessment.

DeepSeek is the initially supported optional cloud provider. Cloud use is disabled
until the user configures it, and every cloud transmission requires a preview and a
narrow approval bound to the provider, model, exact redacted payload digest, data
classes, maximum output, estimated cost or explicit cost-unknown state, expiry, and
task correlation ID. The preview explains why local execution is insufficient, what
leaves the Mac, which transformations or redactions were applied, retention/privacy
implications known to the product, expected operational effect, and how to cancel.
Approval of one request never enables later requests.

For the initial DeepSeek provider, the preview must disclose that transmitted input is
processed outside the Mac and, under the provider privacy policy consulted by the
product, may be processed and stored in the People's Republic of China; retention is
not a fixed API guarantee. The product must link the effective provider policy,
surface any available training opt-out as a setup item rather than implying it was
applied, and default-block data classified as credentials, authentication material,
regulated secrets, or third-party sensitive personal data unless a future dedicated
policy explicitly supports that class.

Provider and model identifiers, capabilities, endpoint, protocol, price snapshot,
currency, effective time, and source must come from a versioned replaceable provider
catalog. Stale or missing price data cannot be shown as a current estimate. Actual
provider usage and the computed actual cost are recorded after completion without
logging prompts, credentials, or unredacted response bodies. Cloud denial,
authentication failure, insufficient balance, rate limiting, overload, timeout,
content filtering, malformed response, and validation failure remain distinct honest
outcomes and never trigger another provider silently.

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
- Cloud providers are off by default; credentials live in Keychain, diagnostic export
  is secret-free, and disabling a provider revokes future routing without deleting
  audit history.

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
8. local Qwen success, local ineligibility, local validation failure, cloud denial,
   approved DeepSeek success, stale-price, auth, balance, rate-limit, overload,
   timeout, malformed-response, and cancellation paths with one correlated audit;
9. proof that the approved payload digest is exactly the transmitted payload and that
   no cloud credential, prompt, or response body enters ordinary logs;
10. security, privacy, accessibility, and usability reviews;
11. one user unfamiliar with implementation completing installation, a local task,
    an approved cloud escalation, and the other core journeys from public
    documentation without hidden help.

## 8. Pending decisions

- Product name and application identity.
- Packaging: native app with managed services, signed package/launcher, or another tested option.
- Redistribution and license rights for each upstream component.
- Supported hardware/model tiers.
- Initial task classes and measurable validation gates that make local Qwen eligible
  or cause the product to propose DeepSeek.
- Maximum age and signed update channel for cloud price snapshots.
- First reversible connector for end-to-end acceptance.
