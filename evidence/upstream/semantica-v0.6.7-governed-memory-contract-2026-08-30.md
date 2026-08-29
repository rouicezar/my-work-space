# Semantica v0.6.7 governed-memory contract evidence

Date: 2026-08-30

## Upstream identity

- Repository: `https://github.com/semantica-agi/semantica`
- Tag object: `a4813ff6338db7c5ad06923d69d53c31866b048a`
- Peeled commit: `ecb33a5b7d1c232da77527da89d861e2b10e9c42`
- Inspection source: a depth-one checkout of the exact tag in a temporary
  directory; no moving branch was used.

## Verified source surface

The pinned `AgentContext` source exposes `store`, `retrieve`, `forget`,
`get_memory`, `update`, `export`, `save`, `load`, and `health`.

Material behavior found by source inspection:

- `store(str, metadata=...)` returns a memory ID.
- `retrieve()` uses `max_results`, and accepts explicit graph-disable options.
- `forget(memory_id=...)` delegates to physical memory deletion.
- `update()` reads the old item, deletes it, and stores a replacement; it does
  not preserve a stable product record ID by itself.
- `health()` reports backend availability and total memory count.
- the base distribution has a large Python dependency graph, supporting the
  existing decision to use a separate managed runtime.

## Product contract evidence

The repository now contains a product-owned governance boundary and synthetic
Semantica adapter contract. Automated tests prove:

- candidates remain outside Semantica and cannot be retrieved as confirmed
  knowledge;
- promotion requires source evidence, actor identity, and correlation ID;
- exact duplicates are idempotent and conflicting claims fail closed;
- correction creates a new product version linked to its predecessor;
- restart preserves the governance journal while Semantica remains the content
  authority;
- deletion removes the authoritative item, erases content and sources across
  the version chain, and excludes tombstones from ordinary export;
- an unavailable Semantica backend prevents promotion rather than falling back
  to candidates or another memory store;
- governance SQLite permissions are owner-only.

## Evidence boundary

This is contract and pinned-source evidence, not a real installed Semantica
runtime test. A separate managed environment, exact dependency lock, real
AgentContext storage/retrieval/save/load execution, crash recovery, concurrent
mutation, backup/restore, and oMLX embedding compatibility remain required
before the Semantica adapter can be promoted from contract candidate.

## Real-runtime discovery after contract commit

Installing the exact source into an isolated Python 3.12 environment resolved
135 packages and occupied approximately 1.6 GB. Constructing upstream
`VectorStore(backend="inmemory")` then attempted an unprompted Hugging Face
FastEmbed model download. The test was interrupted before completion. This path
is prohibited for the product because model acquisition must be visible,
approved, pinned, integrity checked, and recoverable.

Real `AgentContext` compatibility is therefore tested with an explicitly
injected no-network vector boundary. That validates upstream memory lifecycle
behavior but does not count as embedding compatibility. Production retrieval
must use a separately verified oMLX embedding route or another explicitly
approved local adapter; upstream automatic model initialization is not an
allowed fallback.
