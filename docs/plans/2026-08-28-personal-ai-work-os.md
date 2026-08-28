# Personal AI Work OS Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build and verify an isolated four-component personal AI work operating system on one Apple Silicon Mac.

**Architecture:** holaOS is the default interaction plane, Herdr manages advanced multi-agent processes, Semantica owns governed long-term knowledge and audit references, and oMLX provides local inference. Integration uses compatibility APIs, MCP/REST, project-local artifacts, explicit risk gates, and correlated audit events.

**Tech Stack:** macOS, shell, Python, JSON Schema, pytest, Semantica, holaOS, Herdr, oMLX, MCP, OpenAI/Anthropic-compatible APIs.

---

## Execution rule

Do not begin the next task until the current task's evidence is stored under `evidence/` and its gate is marked passed. Use exact current upstream documentation and pin observed versions; commands below are targets to validate, not permission to trust stale installation instructions.

### Task 1: Baseline the Mac and repository

**Files:**
- Create: `config/environment.example.yaml`
- Create: `scripts/preflight.sh`
- Create: `tests/test_preflight.py`
- Create: `evidence/environment/README.md`

1. Write failing tests for macOS version, Apple Silicon, RAM/disk capture, required commands, port collisions, and secret-file exclusion.
2. Run `pytest tests/test_preflight.py -v`; expect failures because the script is absent.
3. Implement the minimal read-only preflight and environment template.
4. Run the tests and a live preflight; redact sensitive output into `evidence/environment/`.
5. Review the hardware envelope and confirm model constraints before committing.

### Task 2: Create lifecycle and audit contracts

**Files:**
- Create: `contracts/task-envelope.schema.json`
- Create: `contracts/audit-event.schema.json`
- Create: `contracts/memory-candidate.schema.json`
- Create: `tests/contracts/test_schemas.py`

1. Write failing schema tests covering correlation IDs, risk class, provenance, approval, model route, mutation, validation, and failure class.
2. Run `pytest tests/contracts -v`; expect failures.
3. Add the minimal schemas and valid/invalid fixtures.
4. Re-run tests; expect all contract tests to pass.
5. Commit the contracts before installing services.

### Task 3: Install and verify oMLX independently

**Files:**
- Create: `config/omlx.example.yaml`
- Create: `scripts/health/omlx.sh`
- Create: `tests/integration/test_omlx_contract.py`
- Create: `docs/runbooks/omlx.md`

1. Verify current official requirements and record version/source checksums.
2. Write failing tests for health, model listing, deterministic text completion, tool-call format, embedding, timeout, and restart.
3. Install oMLX using a reviewed, reversible method and project-specific configuration.
4. Select models only after RAM and capability benchmarks; do not hard-code a model prematurely.
5. Run integration tests and store latency, memory, output, and failure evidence.

### Task 4: Install and verify Semantica independently

**Files:**
- Create: `config/semantica.example.yaml`
- Create: `scripts/health/semantica.sh`
- Create: `tests/integration/test_semantica_contract.py`
- Create: `docs/runbooks/semantica.md`

1. Verify current official package, storage choices, MCP/REST contracts, and version compatibility.
2. Write failing tests for add/query, provenance, duplicate suppression, conflict, candidate rejection, confirmed promotion, update, export, delete, and restart.
3. Install into an isolated environment and use a project-local test database.
4. Configure oMLX-backed embedding/inference only if the live Semantica version supports the required adapter; otherwise add a thin tested bridge.
5. Run tests and save graph/audit evidence without importing personal data.

### Task 5: Install and verify Herdr independently

**Files:**
- Create: `config/herdr.example.yaml`
- Create: `scripts/health/herdr.sh`
- Create: `tests/integration/test_herdr_workflow.py`
- Create: `docs/runbooks/herdr.md`

1. Verify current supported installation and Codex integration behavior.
2. Write a synthetic agent fixture that works, waits for approval, fails, and can be cancelled.
3. Install Herdr and its selected integration without changing unrelated terminal configuration.
4. Test parallel panes, state detection, detach/reconnect, log capture, cancellation, and restart.
5. Record human UI observations in addition to machine checks.

### Task 6: Install and verify holaOS independently

**Files:**
- Create: `config/holaos.example.yaml`
- Create: `scripts/health/holaos.sh`
- Create: `tests/integration/test_holaos_fixture.py`
- Create: `docs/runbooks/holaos.md`

1. Review the current installer/source and record permissions, data locations, and rollback.
2. Install with synthetic workspace data and no production connectors.
3. Configure oMLX as a compatible provider and Semantica as MCP only after their contract gates pass.
4. Test task creation, local file fixture, approval denial, approval success, output display, and restart.
5. Perform a visual/usability walkthrough and record mismatches.

### Task 7: Implement the project-local orchestration bridge

**Files:**
- Create: `src/orchestrator/`
- Create: `tests/orchestrator/`
- Create: `docs/runbooks/orchestrator.md`

1. Write failing tests for risk classification, retrieval filters, model routing, Herdr handoff, audit emission, idempotency, and memory promotion.
2. Implement the smallest bridge required by proven interface gaps.
3. Ensure no missing service triggers silent fallback or false success.
4. Add structured logs keyed by correlation ID.
5. Run unit and integration tests before commit.

### Task 8: End-to-end synthetic acceptance

**Files:**
- Create: `tests/acceptance/test_personal_ai_work_os.py`
- Create: `fixtures/acceptance/`
- Create: `evidence/acceptance/README.md`

1. Create a synthetic project-research task requiring retrieval, parallel work, a safe file write, validation, audit, and memory candidate review.
2. Verify one correlation ID links every component record.
3. Inject model, Semantica, Herdr, and holaOS failures one at a time and verify honest degraded states.
4. Test denial, retry, restart, duplicate suppression, export, and deletion.
5. Run the full suite and retain exact results.

### Task 9: Human operating manual and acceptance

**Files:**
- Create: `docs/OPERATIONS.md`
- Create: `docs/TROUBLESHOOTING.md`
- Create: `docs/ACCEPTANCE.md`

1. Document start, stop, health, ordinary task, advanced Herdr task, approval, memory review, recovery, export, deletion, and rollback.
2. Have the user execute the manual without hidden steps.
3. Record usability defects and return to the responsible task.
4. Mark phase one accepted only after technical and human gates pass.
5. Create a separate migration requirements document; do not connect production systems in this task.
