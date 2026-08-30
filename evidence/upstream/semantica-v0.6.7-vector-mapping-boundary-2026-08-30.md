# Semantica v0.6.7 vector mapping boundary — 2026-08-30

## Scope

This is local source evidence for the pinned managed Semantica v0.6.7 runtime
at commit `ecb33a5b7d1c232da77527da89d861e2b10e9c42`. It records why the product
uses a compatibility adapter for governed semantic retrieval.

## Direct source observations

In `semantica/context/agent_memory.py`:

- Lines 464–488 generate a query embedding and call `search_vectors`, then
  convert returned dictionaries into result objects.
- Lines 490–520 map result IDs back to `memory_items`, but that loop is nested
  under the alternative `elif ... search` branch. The `search_vectors` branch
  therefore produces no long-term memory results through this path.
- Lines 789–800 generate the stored embedding and pass only
  `memory_item.metadata` to `store_vectors`; the vector store's returned UUID is
  tracked separately from Semantica's memory ID.

Consequently, treating the vector result `id` as a Semantica memory ID would be
incorrect for the concrete `store_vectors/search_vectors` surface.

## Product boundary

The product-owned index stores vectors plus governed metadata containing
`record_id`. It returns only that metadata to the governed adapter. The
governance layer then resolves its internal record, obtains the authoritative
Semantica ID, reads the current envelope from Semantica, and validates record
ID and version. The vector index is an acceleration index, not a knowledge
authority.

## Existing-model scan

The standard local Hugging Face cache and the identified QClaw embedding
extension directory were inspected on this development Mac. The scan found
chat, speech, TTS, and VAD model assets, but did not confirm a BGE, E5, GTE,
Nomic, or Qwen Embedding model suitable for this route. The QClaw directory
contained extension source rather than model weights.

This is evidence for the inspected locations, not a claim that no embedding
model can exist anywhere on the machine. No model was downloaded or copied.
Real oMLX embedding validation remains unavailable until a compatible model is
explicitly selected and, if necessary, downloaded with user approval.
