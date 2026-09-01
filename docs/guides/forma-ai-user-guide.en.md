# Forma AI — Complete Product Overview and User Guide

> Document status: This is the target user guide for Forma AI after development is complete and all release acceptance gates have passed. Until those gates pass, it defines the intended final user experience and acceptance standard; it is not evidence that the current development build already provides every capability described here.

## 1. Forma AI in one sentence

Forma AI is a local-first, multi-agent AI workbench for Apple Silicon Macs. You describe the outcome; it selects an appropriate local or cloud model, coordinates multiple AI agents, uses only the tools you authorize, maintains governed and traceable long-term memory, and places every material external action behind preview, approval, execution, and verification.

It is not a launcher for four technical components and not a chat wrapper around one model. It combines local inference, multi-agent execution, governed memory, tool connections, permission controls, audit, and recovery into one Mac product designed for ordinary users.

## 2. Who it is for

- People who want to research, write, organize, plan, code, and automate repeatable knowledge work on a Mac.
- Individuals and teams that want sensitive work to stay local by default, while retaining an explicit cloud option when needed.
- Professionals who want multiple AI agents to collaborate while keeping ownership, status, cost, permissions, and evidence visible.
- Users who want to connect files, applications, and business tools without giving an AI unlimited authority.
- Users who want correctable, deletable, source-linked long-term knowledge instead of opaque chat “memory.”

Forma AI may not be suitable if your Mac is outside the supported Apple Silicon matrix, or if your workflow depends on unsupported proprietary systems, real-time hardware control, or unsupervised high-risk automation.

## 3. What Forma AI can do

### 3.1 Run everyday knowledge work in one place

You can create tasks such as:

- “Compare these three proposals and show evidence, disagreements, risks, and a recommendation.”
- “Use this source folder to write a cited Chinese report and an English executive summary.”
- “Analyze this code repository, propose a repair plan first, and commit only after tests pass.”
- “Turn these meeting materials into decisions, owners, deadlines, and open questions.”
- “Classify and rename these files and create an index; show me the exact change list before writing anything.”

Forma AI turns the objective, inputs, constraints, acceptance criteria, and permission requirements into a recoverable task—not a disposable one-shot chat.

### 3.2 Use AI locally by default

By default, Forma AI runs a verified local model through oMLX on your Mac. Suitable tasks remain on-device, including summarization, classification, structured extraction, memory retrieval, low-risk routing, and selected writing tasks.

If the local model cannot meet a context, modality, tool, or quality requirement, Forma AI does not silently switch to the cloud. It explains the gap and, if cloud use is configured, shows a one-time proposal with provider, model, outgoing data, processing location, privacy notice, maximum output, estimated cost, and audit correlation. Only the exact request you approve may be sent.

### 3.3 Coordinate multiple agents

Forma AI uses Herdr as its multi-agent execution core. A complex task can be divided into research, analysis, implementation, testing, and review. You can see each agent’s owner, status, logs, artifacts, blockers, and permission requests, and you can pause, cancel, or resume work.

Results are aggregated only after defined acceptance checks. More agents do not guarantee a correct answer; the final result still shows verification state and unresolved issues.

### 3.4 Maintain governed long-term memory

Forma AI uses Semantica for long-term knowledge. Raw input, run logs, candidate knowledge, and confirmed knowledge remain separate.

- Information does not become a long-term fact merely because it appeared in a conversation.
- Candidate knowledge requires source, time, and task correlation.
- Important facts and decisions require confirmation before becoming authoritative memory.
- You can inspect sources, correct records, review version history, export, and delete.
- Corrections and deletions cannot be silently undone by an older version.

### 3.5 Connect tools and applications safely

Installed connectors can expose files, browsers, calendars, task systems, databases, and other applications. Each connector declares read, write, send, delete, execute, and credential scopes separately.

Read access does not imply write access; write access does not imply send or delete access. Material actions show the target, scope, change, impact, and verification method first. You can approve once, deny, narrow the scope, or revoke the connector.

### 3.6 Preserve history, audit, and recovery state

Every material task has a stable ID and correlated audit trail. You can distinguish completed, partially completed, denied, failed, cancelled, and rolled-back work. Persistent tasks can resume from a reconciled state after the app or Mac restarts; they are not falsely marked complete.

## 4. Core advantages

1. **Local-first as an enforceable route, not a slogan.** Local work requires real inference and resource checks; cloud use requires per-request preview and approval.
2. **Visible, controllable, recoverable multi-agent work.** You can see who is doing what, cancel or resume work, and inspect artifacts instead of waiting on a black box.
3. **Source-linked, versioned, deletable memory.** The system separates observed, candidate, and confirmed knowledge to reduce long-term contamination.
4. **Preview before action; verification after action.** External writes, sends, deletes, commands, and cloud transfers have explicit permission boundaries.
5. **Honest failure states.** Missing capability, network failure, bad credentials, model unavailability, and validation failure are not disguised as success or empty output.
6. **One product owns the lifecycle.** Installation, setup, start, stop, update, rollback, recovery, and uninstall are managed in one interface.
7. **Replaceable components.** Models, agents, and tools connect through versioned adapters, reducing dependence on a single provider.

## 5. Capability boundaries

Boundaries are not defects. They protect quality, privacy, and recoverability.

| Boundary | Forma AI behavior |
|---|---|
| Local model cannot satisfy the task | Explain the gap; create a one-time proposal if cloud is configured, otherwise offer a feasible alternative |
| High-risk external action | Require an explicit preview and scoped approval; denial or timeout means no action |
| Reliable evidence is missing | Label the result as assumption, unverified, or unknown rather than presenting inference as fact |
| Tool or provider is unavailable | State the affected capability and recovery path; do not silently substitute another provider |
| Full verification is impossible | Return partial completion and outstanding checks, not a false completion claim |
| Device resources are insufficient | Recommend a smaller model or lower concurrency; do not force an unsafe configuration |
| Memory records conflict | Preserve the conflict and sources; require confirmation before updating authority |
| Connector permission is insufficient | Request the smallest additional scope or offer a read-only alternative |

## 6. What Forma AI cannot do

- It cannot guarantee that AI output is always correct. Important factual, legal, medical, financial, security, and production decisions still require qualified review.
- It cannot assume responsibility for your decisions or treat one approval as unlimited authority.
- It cannot bypass macOS permissions, organizational controls, third-party policies, or terms of service.
- It cannot send data to a cloud provider without preview and approval, and it cannot guarantee third-party availability or unchanging policies.
- It cannot turn every conversation into permanent memory; unconfirmed content does not become authoritative knowledge.
- It cannot access files, applications, accounts, or devices that are not connected, authorized, and available.
- It cannot claim an unverifiable real-world outcome. “Email delivered,” “payment settled,” and “deployment live” require corresponding evidence.
- It is not antivirus software, a backup system, a password manager, or a compliance certification authority.
- It does not disable audit, bypass approval, or silently route to another cloud provider to make a task look faster.
- The first release does not support Intel Macs. Supported macOS, memory, storage, and model tiers are defined by the in-app support matrix.

## 7. First launch: the recommended 10-minute path

### Step 1: Complete the device check

On first launch, Forma AI checks the chip, macOS version, available memory, free storage, and port conflicts. Confirm that the device is supported or read the explanation for any unknown measurement. Unknown is neither a pass nor an automatic rejection.

### Step 2: Choose a local model profile

Accept the recommended profile or choose another supported model based on storage, speed, and quality. The app shows download size, installed footprint, capabilities, and license. A verified existing model may be referenced without copying; externally owned caches are not silently deleted.

### Step 3: Install and verify the local runtime

Approve the exact installation plan, then allow download, verification, and installation to complete. Interrupted work can resume. Run the verified sample task afterward. “Local AI ready” appears only after a real model response succeeds.

### Step 4: Configure memory

Select a local semantic retrieval model and review storage location, vector dimension, disk impact, and deletion policy. Enable long-term memory only after a real retrieval check succeeds. “Confirm every memory write” is the recommended starting policy.

### Step 5: Review permission defaults

Under Settings → Permissions & Approvals, keep these recommended defaults:

- Scope read access by folder or connector.
- Require preview for write, send, delete, and execute.
- Ask for every cloud request.
- Store credentials only in macOS Keychain.
- Never grant permanent approval for high-risk actions.

### Step 6: Configure cloud AI only if needed

Add your own API key under Models & Providers, run the low-cost connection test, and read the provider’s data-processing notice. Cloud is off by default. Saving a credential does not authorize any task transmission.

### Step 7: Connect one tool

Start with a low-risk, reversible connector. Grant read-only access first, run one read-only task, then test one reversible write with a clear preview and verification method.

### Step 8: Run your first real task

Start small and explicit:

> Read the three documents I selected. Separate facts, opinions, and unverified claims, then produce a one-page summary. Read only; do not modify source files and do not use cloud AI. Acceptance: every key conclusion names its source file.

After completion, inspect the result, sources, model route, agent status, and audit record.

## 8. The main interface

- **New task:** Create work, continue the conversation, observe execution, and respond to approval requests.
- **History:** Find completed, active, interrupted, failed, or cancelled tasks and resume eligible work.
- **Settings:** Manage General, Models & Providers, Agents & Tools, Memory, Permissions & Approvals, Local Runtime, Data & Privacy, and Diagnostics & Recovery.

Normal work should begin in New task. Open Settings when configuring capabilities, reviewing data, or recovering from a problem.

## 9. How to write a good task

A strong task usually includes five parts:

1. **Objective:** What final outcome you need.
2. **Inputs:** Which files, folders, links, or connectors may be used.
3. **Constraints:** What must not be changed, sent, or assumed.
4. **Process:** Whether to use parallel agents, plan first, research first, or ask before acting.
5. **Acceptance:** How completion will be judged, including output format and evidence.

Recommended template:

> Objective: …  
> Allowed inputs: …  
> Prohibited actions: …  
> Execution requirements: …  
> Acceptance criteria: …  
> Output location/format: …

Avoid “make this better.” Prefer: “Preserve the meaning and reduce this 2,000-word Chinese guide to 1,200–1,400 words for first-time non-technical users. Do not add product claims not present in the source. Return the revision and five major changes.”

## 10. Status and approval meanings

- **Local:** The task uses a verified on-device route.
- **Cloud proposal required:** Nothing has been sent; review a one-time cloud proposal.
- **Capability unavailable:** No current safe route can satisfy the task; the system did not silently downgrade.
- **Needs attention:** An agent, tool, model, or permission requires action.
- **Partial:** Some artifacts are valid, with explicit remaining work.
- **Failed safely:** Work stopped without being presented as success; review the recovery guidance.

Before approval, check the recipient, data scope, external effect, maximum cost, expiry, reversibility, and how the system plans to verify the outcome.

## 11. Using multiple agents well

- Parallelize independent work such as source verification, option comparison, and risk review; avoid multiple agents editing the same file.
- Give every agent a concrete artifact and acceptance criteria.
- Assign one owner for writes; use other agents for advice or review.
- Add checkpoints to long work: approve research and design before implementation.
- Ask the synthesis step to show agreements, disagreements, missing evidence, and rejected options.
- When an agent is blocked, resolve the permission, input, or dependency instead of retrying blindly.

## 12. Using memory well

- Save information that will be reused and has a source: project decisions, definitions, confirmed preferences, and process rules.
- Do not confirm temporary guesses, disposable drafts, or third-party sensitive data as long-term memory.
- Review candidates, conflicts, and stale records regularly.
- Correct a fact with new evidence instead of silently overwriting it.
- Before leaving a project or organization, export what must be retained and delete data with no continuing legitimate purpose.

## 13. Privacy and security practices

- Use the local route first; consider a cloud proposal only when needed.
- Enter API keys only in the secure credential interface, never in tasks, logs, or files.
- Grant connectors minimum scope, preferably by folder, project, account, and action.
- Review every send, delete, payment, publication, and production deployment preview.
- Inspect the redaction summary before sharing a diagnostic bundle.
- Review cloud providers, connectors, and standing approvals regularly; revoke what you no longer use.
- Keep independent backups of important files. Task recovery state is not a backup.

## 14. When something goes wrong

1. Read the error class, affected capability, and data-risk statement.
2. Open Settings → Diagnostics & Recovery and refresh component and workflow health.
3. Prefer the app’s safe retry, resume, stop, or rollback action.
4. Do not repeatedly reinstall, delete state folders, or kill processes without understanding the effect.
5. Export a redacted diagnostic bundle and the task correlation ID before contacting support.
6. For an external write, check the destination system before retrying to avoid duplicate sends or records.

## 15. Update, rollback, and uninstall

Before an update, Forma AI checks version, disk, component compatibility, and the data migration plan. A failed update can recover or roll back to a verified version; a partial migration is never reported as success.

During uninstall, choose whether to:

- retain local models and governed data;
- export and then delete product data;
- remove product-managed data and credentials;
- retain externally owned model caches or separately installed applications.

The uninstall summary states what was removed, what remains, and how retained data can be recovered.

## 16. Frequently asked questions

### Does Forma AI upload my files automatically?

No. The local route is the default. Every cloud transfer requires a one-time approval that identifies the data and cost.

### If I configure DeepSeek, will every task use it?

No. A credential only makes the provider available. Local remains the default and every cloud transfer requires separate approval.

### Are multiple agents always better?

No. Simple tasks use a smaller execution plan. Multiple agents help when work can be parallelized, needs different expertise, or benefits from independent review.

### Does Forma AI remember every conversation?

No. Conversations, audit, candidate knowledge, and confirmed long-term memory are separate layers. Only policy-compliant, confirmed content becomes authoritative memory.

### Can I run it completely unattended?

Low-risk, predefined, verifiable work may run under policy. Cloud transmission and high-risk external actions remain governed by approval rules. Forma AI does not offer unlimited permanent authority.

### How do I get the best results?

Provide a clear objective, reliable inputs, explicit constraints, and testable acceptance criteria. Start small, inspect evidence and audit, then expand connector access and automation gradually.

## 17. A recommended first week

- Day 1: Complete local runtime, memory, and permission setup; run a read-only document task.
- Day 2: Create one source-linked project memory and practice correction and deletion.
- Day 3: Connect one low-risk tool and run a read-only task.
- Day 4: Perform one reversible write with preview and verification.
- Day 5: Try a multi-agent task and inspect delegation, blockers, and synthesis.
- Day 6: Review one cloud proposal on non-sensitive work and inspect data and cost carefully.
- Day 7: Review history, audit, permissions, and memory; revoke unnecessary access and save useful task templates.

The best operating principle is simple: let Forma AI prove that it can complete small tasks safely before expanding task complexity, data scope, and operational authority.
