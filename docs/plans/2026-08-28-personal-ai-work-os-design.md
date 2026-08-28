# Personal AI Work OS Design

Status: draft for user validation.

## Architecture

```text
User
  |
  v
holaOS -- ordinary tasks, files, browser, apps, approval UI
  |
  +--> policy and risk gate
  |       |
  |       +--> Semantica query: confirmed facts, decisions, precedents
  |       +--> local execution through oMLX
  |       +--> long/development task handoff to Herdr
  |
  +<-- validated result and audit event

Herdr -- agents, terminals, tests, background processes
  |         |
  |         +--> oMLX compatibility API
  |         +--> Semantica MCP/REST
  |
Semantica -- confirmed knowledge and decision/audit references
oMLX      -- model, embedding and reranking inference
```

The four projects are integrated through stable boundaries—MCP, REST, OpenAI/Anthropic-compatible APIs, project files, and process status—not by immediately modifying upstream source code.

## Control and data flow

Each task receives a correlation ID. Before execution, a policy layer assigns a risk class and allowed tools. Retrieval returns only knowledge that meets provenance and status filters. Ordinary work runs from holaOS; long-running development and parallel verification run in Herdr. oMLX performs local inference. Tool outputs are validated before the response is accepted. The audit trail then records inputs, model routing, calls, mutations, approvals, validation, and outcome. A separate memory pipeline extracts candidates, detects conflicts, and promotes only validated items to confirmed Semantica knowledge.

## Failure handling

Failures are classified as configuration, dependency, permission, model capability, tool, integration, validation, or upstream error. A degraded component must not silently change semantics: no Semantica means no claim of memory-backed output; no oMLX means no implicit cloud fallback; no Herdr means no claim that background work continues; no holaOS connector means no claim that an external action happened. Retry must be idempotent, and correlation IDs prevent duplicate audit and memory writes.

## Security model

Phase one uses only synthetic fixtures and project-local state. Secrets are stored outside Git and injected at runtime. Read, write, send, delete, execute, and credential-use permissions are distinct. Real external writes remain disabled. Audit logs record metadata and hashes where raw sensitive content is unnecessary. Data retention, export, and deletion tests are mandatory before persistent personal data is admitted.

## Acceptance gates

1. Environment gate: supported Mac, disk, RAM, ports, runtimes, and rollback path.
2. Component gate: independent install, start, health, stop, restart, and log inspection.
3. Contract gate: API/MCP schemas and version pins verified with fixtures.
4. Memory gate: provenance, conflict, rejection, update, and deletion behavior.
5. Agent gate: parallel execution, approval wait, detach/reconnect, cancellation.
6. Tool gate: read-only succeeds; writes require scoped approval; denial is preserved.
7. End-to-end gate: one synthetic workflow produces correlated result, audit, and confirmed memory.
8. Human gate: the user follows the manual and confirms usability, clarity, and recovery.

## Deliberate boundary

This design does not promise that the four upstream projects already provide every adapter. Compatibility must be proven against current versions during implementation. Any missing adapter is first implemented as a thin project-local bridge with contract tests; an upstream fork is the last resort.
