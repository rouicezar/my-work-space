# ADR 0011 — Governed Semantica memory boundary

Status: accepted for implementation

## Context

Semantica v0.6.7 is pinned at commit `ecb33a5b7d1c232da77527da89d861e2b10e9c42`.
Its `AgentContext` can store, retrieve, export, save, load, update, and forget
memory. The upstream `update()` implementation deletes the old memory and
stores a new item, while `forget()` physically removes memory. Those operations
alone do not satisfy the product requirement for stable identity, explicit
candidate review, correction history, deletion evidence, and fail-closed
retrieval.

## Decision

The product exposes a versioned governed-memory contract rather than upstream
objects directly.

- Raw input, candidates, audit events, and confirmed knowledge are separate
  storage classes.
- A candidate requires a stable claim key, non-empty content, at least one
  source reference, and a correlation ID. Creating a candidate never writes to
  Semantica.
- Only explicit confirmation writes a governed envelope to Semantica.
- The current confirmed envelope stored through Semantica is the authority for
  retrievable knowledge. The product governance journal records lifecycle
  evidence and is not a fallback knowledge store.
- A duplicate confirmed claim is idempotent. A different value for an existing
  claim key is a conflict and cannot be promoted implicitly.
- Correction creates a new version linked to the previous version. The prior
  Semantica item is removed only after the new version is stored. Failure must
  remain explicit and recoverable.
- Deletion removes the Semantica item and retains a content-free tombstone plus
  immutable governance event. Deleted content is never returned by retrieval
  or ordinary export.
- If Semantica is missing or unhealthy, confirmed-memory reads and writes fail
  with an explicit capability error. Candidate data is not returned as a
  substitute.
- Semantica health is unavailable until an explicit, verified embedding route
  is injected. The presence of a chat model does not satisfy this requirement,
  and upstream automatic embedding-model downloads are prohibited.
- The product owns a persistent local semantic index bound to the exact oMLX
  embedding model and vector dimension. It stores governed metadata including
  `record_id`, but never becomes an authority for confirmed content.
- Semantic retrieval first resolves `record_id` from that index, then reads and
  validates the current confirmed envelope through Semantica. Missing,
  superseded, deleted, or mismatched records fail closed or are omitted.
- Product data lives below the product-owned application support root. Tests
  use synthetic data and temporary databases only.

## Contract operations

`propose`, `confirm`, `reject`, `correct`, `delete`, `get`, `retrieve`,
`history`, `export`, and `health` carry schema version 1 and a correlation ID.
Every mutation appends an event containing actor, action, target, outcome,
timestamp, and version without storing secrets.

## Upstream adapter boundary

The adapter requires only `store`, `get`, `retrieve`, `forget`, `save`, `load`,
and `health`. A Semantica v0.6.7 implementation translates governed envelopes
to `AgentContext` content and metadata. Tests run the same contract against an
in-memory synthetic backend before the separately managed upstream runtime is
installed and exercised.

The product does not expose Semantica's upstream REST server as the memory
boundary. In v0.6.7 that server fixes port `8000`, collides with oMLX, and its
health route does not exercise `AgentContext` or an embedding backend. The
Supervisor will instead own an authenticated loopback governed-memory service
that imports Semantica from its isolated managed environment and reports
library, governance, storage, and embedding health separately.

The frozen Supervisor does not extend its import path with Semantica's external
site-packages. When an approved embedding activation exists, it launches a
small product-owned memory entrypoint using the exact managed Semantica Python
interpreter. The signed app bundle carries the explicitly enumerated product
modules needed by that entrypoint. Without an activation record, Supervisor
starts the unavailable backend so candidate capture remains usable and the
missing capability stays visible.

Authoritative `AgentContext` state is written to a temporary owner-only
directory and its JSON state file is atomically replaced after every mutation.
Store failure removes the newly created upstream item; delete persistence
failure restores it. The SQLite vector index persists independently, is bound
to model and dimension, and tolerates content-free orphan entries because every
retrieval is revalidated through the governance database and Semantica.

Semantica v0.6.7's `search_vectors` branch constructs vector results but does
not map them back to memory items; that mapping is nested only under its
alternative `search` branch. Its `store_vectors` call also provides governed
metadata rather than the Semantica memory ID. The product adapter therefore
does not call upstream vector retrieval. It queries the product index for
governed `record_id` metadata and then resolves content through Semantica's
`get_memory` boundary. This is an explicit compatibility adapter, not a second
knowledge store.

## Consequences

This preserves Semantica as the confirmed-memory authority without pretending
its raw mutation API already implements product governance. It also prevents
holaOS session memory, audit logs, or product candidates from becoming a
second source of confirmed truth.
