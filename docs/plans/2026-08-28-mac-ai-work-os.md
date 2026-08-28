# Mac AI Work OS Product Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a general-purpose, distributable, out-of-the-box Mac AI work operating system based on Semantica, holaOS, Herdr, and oMLX.

**Architecture:** A product-owned installer, lifecycle supervisor, policy/approval service, orchestrator, audit correlator, and thin adapters create one coherent experience. holaOS is the default UI, Herdr is optional advanced runtime, Semantica owns governed memory, and oMLX provides local inference.

**Tech Stack:** macOS, packaging spike, shell, Python, JSON Schema, pytest, Semantica, holaOS, Herdr, oMLX, MCP, compatible model APIs.

---

## Phase 0 — Product feasibility

### Task 1: Upstream compatibility and licensing

**Files:** `docs/research/upstream-matrix.md`, `docs/research/license-matrix.md`, `evidence/upstream/`

Verify canonical repositories, releases, requirements, APIs, data paths, updates, licenses, bundling and redistribution rights. Identify ownership overlap. Packaging fails if a required right or stable contract is unproven.

### Task 2: Supported Mac profiles

**Files:** `config/hardware-profiles.yaml`, `scripts/preflight.sh`, `tests/test_preflight.py`, `docs/support-matrix.md`

Write failing tests for Apple Silicon, macOS, RAM, disk, ports, and profile selection. Implement read-only detection. Benchmark available hardware without generalizing beyond evidence. Publish provisional tiers and unknowns.

### Task 3: Packaging architecture spike

**Files:** `docs/adr/0001-packaging.md`, `prototypes/lifecycle/`, `tests/lifecycle/`

Prototype at least native-app-managed-services and signed-package/launcher approaches. Test clean/interrupted install, resume, restart, upgrade, rollback, uninstall, signing, permissions, accessibility, maintenance, and upstream compatibility. Record the decision and remove obsolete artifacts.

## Phase 1 — Contracts and component adapters

### Task 4: Product contracts

Create versioned task, audit, memory, health, and connector schemas plus valid/invalid fixtures. Test correlation, risk, provenance, approvals, mutations, validation, permissions, privacy routes, retention, and failure semantics.

### Task 5: oMLX adapter

Test model discovery, completion, tools, embedding, reranking, timeout, resource exhaustion, restart, and route disclosure using hardware profiles.

### Task 6: Semantica adapter

Test provenance, candidates, confirmation, conflict, correction, history, export, retention, deletion, duplicates, restart, and oMLX compatibility with synthetic data.

### Task 7: Herdr adapter

Test parallel execution, status, approval wait, detach/reconnect, logs, cancellation, crash recovery, and result handoff while keeping it optional for ordinary users.

### Task 8: holaOS adapter and UI boundary

Test tasks, local fixtures, approvals, results, memory review, connector management, health, and restart. Identify UI gaps without assuming upstream already satisfies novice needs.

## Phase 2 — Unified runtime

### Task 9: Lifecycle supervisor

Implement manifest-driven verified downloads, configuration, ports, start order, migrations, backup, health, repair, update, rollback, and uninstall as a recoverable state machine.

### Task 10: Policy, approval, and audit

Implement capability scopes, risk rules, previews, expiring task-bound approvals, idempotency, correlation, redaction, retention, and honest terminal states with failure-first tests.

### Task 11: Orchestrator and memory promotion

Implement governed retrieval, visible routing, Herdr handoff, validation, audit, candidate extraction, conflict checks, promotion, correction, and deletion. Missing components must cause explicit capability failure.

### Task 12: Installer and first-run assistant

Build compatibility detection, profile recommendation, download estimates, consent, progress, repair, and a verified sample task. The primary path requires no terminal.

## Phase 3 — Distribution and acceptance

### Task 13: First real connector

Using dedicated test accounts, test authorization, minimal scopes, read, preview, approval, reversible write, verification, revocation, timeout, duplicate prevention, and audit.

### Task 14: Package, sign, update, and uninstall

Produce a reproducible artifact and license notices; sign/notarize when credentials are available; test clean install and upgrades; verify uninstall keep/export/delete choices.

### Task 15: Security, recovery, and privacy

Threat-model secrets, prompts, connector tokens, audit, local APIs, downloads, updates, and extensions. Verify backups, rollback, redaction, least privilege, and no silent transmission.

### Task 16: Documentation and novice acceptance

Publish install, first-run, daily use, memory, approvals, connectors, troubleshooting, recovery, update, uninstall, privacy, and extension docs. An unfamiliar user must complete core journeys without hidden assistance.

### Task 17: Requirement-to-evidence release audit

Create `docs/release/evidence-index.md`. Map every requirement to authoritative automated or human evidence. Missing, indirect, single-machine-only, or outdated evidence keeps release incomplete.
