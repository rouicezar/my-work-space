# Semantica managed-runtime runbook

## Purpose

The Supervisor verifies Semantica as a pinned library inside a product-managed
Python environment. It does not start or trust the upstream REST server. The
product-owned governed-memory service is a separate authenticated loopback
boundary. Its contract handler covers the governed operations with bounded
requests and redacted request-level audit. Supervisor now starts it after the
inference broker, stops it first, verifies `/live`, and records process identity.
The product includes a managed Semantica/embedding factory and a separate
memory-runtime entrypoint executed by the pinned Semantica Python interpreter.
Public app builds copy only the explicitly required product modules into
`Contents/Helpers/MemoryRuntime`; they do not inject external site-packages
into the frozen Supervisor.

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

The repository has real fixed-version `AgentContext` lifecycle evidence,
including atomic authoritative-state persistence, vector-index persistence,
restart retrieval, deletion, and persistence-failure rollback. It does not yet
contain the managed-environment installer or an approved production embedding
model.

If `state/models/embedding-active.json` is absent, Supervisor starts an
honestly unavailable memory capability: candidates can be journaled while
confirmation fails closed. If it is present, it must be an owner-only regular
file bound to an owner-only zero-copy model reference, exact revision, oMLX API
model name, and positive expected dimension. Supervisor then requires the exact
managed Semantica v0.6.7 runtime and starts the memory service with that
interpreter. oMLX and memory secrets travel only in the child environment.

There is intentionally no manual activation recipe. The future model-selection
command and native approval UI must validate an embedding-capable catalog
entry, verified weights, license, disk impact, model revision, and dimension
before atomically creating the activation record. Until that workflow and a
real model probe pass, memory is not ready for end users.
