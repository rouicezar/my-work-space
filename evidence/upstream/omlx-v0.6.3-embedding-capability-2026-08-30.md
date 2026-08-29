# oMLX v0.6.3 embedding capability boundary

Date: 2026-08-30

## Fixed upstream evidence

- Official tag: `v0.6.3`
- Inspected commit: `85708e4b9a585df42241c826b6be2b4dba018406`
- The fixed source implements `POST /v1/embeddings` with an
  OpenAI-compatible request and response contract.
- Its model discovery separates `llm`, `embedding`, and `reranker` types.
  Causal-LM-family embedding models require explicit embedding evidence such
  as an embedding architecture, sentence-transformers pipeline, or an
  embedding model name. Ambiguous Qwen model types otherwise remain LLMs.

## Current verified model

The existing zero-copy model reference points to
`mlx-community/Qwen3-0.6B-4bit` at revision
`73e3e38d981303bc594367cd910ea6eb48349da8`. Its verified configuration says:

- architecture: `Qwen3ForCausalLM`
- model type: `qwen3`
- no sentence-transformers pipeline
- model path contains no embedding designation

The product catalog therefore declares only `chat`. It does not advertise
`embedding`, and the native setup UI visibly reports that semantic memory
search remains unavailable.

## Product rule

Model capabilities are explicit, closed catalog data and travel through the
Supervisor protocol. Unknown capabilities fail validation. A chat model can
never satisfy the Semantica embedding health gate merely because oMLX exposes
an embeddings route.

No embedding model was downloaded during this verification. Adding one
requires a separately pinned catalog entry, license and file manifest,
hardware-profile budget, visible download estimate, explicit approval,
integrity verification, real embedding call, restart test, and uninstall data
ownership test.

## Remaining evidence

The product still needs a suitable local embedding model and a real
`/v1/embeddings` execution. Until then, Semantica memory lifecycle works, but
semantic retrieval is an explicitly unavailable capability rather than a
degraded keyword or hidden cloud fallback.
