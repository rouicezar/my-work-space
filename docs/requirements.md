# Personal AI Work OS Requirements

Status: draft migrated from Codex task `调研四个项目及组合方案` on 2026-08-28.

## 1. Objective

Build an independently testable system on a personal Apple Silicon Mac that can retain governed memory, produce auditable decisions, run agents in parallel, and operate tools through explicit permission gates.

## 2. Functional requirements

1. A user can start an ordinary task from holaOS.
2. The system classifies task risk before tool execution.
3. An agent can retrieve relevant verified facts, decisions, evidence, and precedents from Semantica.
4. Development or long-running work can be delegated to agents/processes visible in Herdr.
5. Compatible clients can use oMLX through a local OpenAI- or Anthropic-compatible endpoint.
6. Every material run produces an audit record containing task ID, timestamps, agent, model, inputs, tools, mutations, approvals, outputs, validation, failures, and memory IDs.
7. Candidate memory is separated from confirmed knowledge and cannot become authoritative without provenance and validation.
8. High-risk or real-world writes stop at an approval gate.
9. Each component can be stopped or replaced without corrupting another component's state.

## 3. Non-functional requirements

- Local-first, but not inaccurately described as fully offline.
- Project-local and reversible installation during phase one.
- No secrets committed to Git.
- Observable health checks and classified failures for each service.
- Deterministic fixtures for acceptance tests.
- Data export and deletion procedures must exist before persistent use.
- Version pins and compatibility evidence must be recorded at installation time.

## 4. Data classes

| Class | Examples | Destination |
|---|---|---|
| Raw input | chat, web pages, files | task-local evidence; not long-term memory by default |
| Run record | tool calls, status, mutations | append-only audit log |
| Candidate knowledge | agent-extracted project fact | validation queue |
| Confirmed knowledge | sourced and approved fact or decision | Semantica authoritative store |

## 5. Out of scope for phase one

- Connecting MyNote or GBrain.
- Migrating existing memories or automations.
- Production email, calendar, Feishu, or other real-account operations.
- Unattended destructive actions.
- Deep source-code forks of the four upstream projects unless an interface gap is proven.

## 6. Success criteria

Phase one succeeds only when:

- all four components pass independent health checks;
- a synthetic end-to-end task passes through holaOS, oMLX, Semantica, and Herdr with traceable IDs;
- a false candidate memory is rejected and remains absent from confirmed knowledge;
- a high-risk write is blocked without approval and succeeds only in an isolated fixture after approval;
- restart and recovery preserve intended state without duplicating audit or memory records;
- the user completes the operating-manual workflow on the Mac and judges it usable.

## 7. Open requirement

Cloud fallback policy is not yet confirmed. Recommended phase-one default: local-only acceptance baseline, with cloud escalation disabled until a separate, manually approved test case is added.
