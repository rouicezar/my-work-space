# Semantica managed-runtime runbook

## Purpose

The Supervisor verifies Semantica as a pinned library inside a product-managed
Python environment. It does not start or trust the upstream REST server. The
product-owned governed-memory service is a separate authenticated loopback
boundary. Its contract handler covers the governed operations with bounded
requests and redacted request-level audit. Supervisor now starts it after the
inference broker, stops it first, verifies `/live`, and records process identity.
The production Semantica/embedding factory remains pending.

## Read-only status

```bash
python3 scripts/supervisor.py \
  --request-id 00000000-0000-4000-8000-000000000001 \
  semantica-status \
  --root "/absolute/product/app-support/root"
```

This command never installs a package, creates product state, downloads an
embedding model, or accepts a developer environment outside the managed root.

## Status layers

| Field | Meaning |
|---|---|
| `installation` | Exact active record and managed interpreter layout |
| `library` | Semantica `0.6.7` imports from inside the managed runtime |
| `agent_context` | The pinned `AgentContext` surface imports successfully |
| `embedding` | A separately approved local embedding route has been proven |
| `status` | End-to-end governed-memory capability; remains unavailable until every required layer passes |

`SEMANTICA_NOT_INSTALLED`, `SEMANTICA_ACTIVE_RECORD_MISMATCH`, import/version
errors, and `EMBEDDING_ROUTE_UNVERIFIED` are capability failures. They must not
be presented as an empty memory result or replaced by a hidden cloud route.

## Current boundary

The repository has real fixed-version `AgentContext` lifecycle evidence using
an explicitly injected no-network vector boundary. It does not yet contain the
managed-environment installer or approved production embedding model. The
Supervisor-managed process therefore starts in an honestly unavailable memory
capability state: candidates can be journaled, while confirmation fails closed.
This is not yet a claim that memory is ready for end users.
