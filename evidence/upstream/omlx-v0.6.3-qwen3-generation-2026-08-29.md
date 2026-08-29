# oMLX v0.6.3 Existing Qwen Model and Real Generation Evidence

Date: 2026-08-29

Environment: Apple Silicon, macOS 26.6.2

Runtime: pinned official oMLX v0.6.3 artifact

Model: `mlx-community/Qwen3-0.6B-4bit` at revision `73e3e38d981303bc594367cd910ea6eb48349da8`

## Existing model reuse

The model already existed in the machine's shared Hugging Face cache. The product did not download or copy it. It verified all nine catalogued files by exact size and SHA-256, checked the Qwen3 architecture and four-bit quantization metadata, then created an external directory reference under the product-managed oMLX model directory.

The product state explicitly records `external-cache-not-product-owned`. Uninstall and cleanup must remove only the product reference and must never delete the external cache. This test does not claim which earlier project originally populated the shared cache.

The largest file was `model.safetensors`, `335450584` bytes, SHA-256 `392e8d466d56100ada00eb82031fb854297fc9e389b7d303eba3af114e87bce2`.

## Real runtime generation

The versioned oMLX installation started with an isolated product HOME and discovered the referenced model as its default LLM. The deep-health probe completed a real chat generation and returned `ready` with `deep_probe_passed: true`.

A second request traversed the product broker and the real oMLX runtime:

- HTTP status: `200`
- Model: `Qwen3-0.6B-4bit`
- Thinking disabled through `chat_template_kwargs`
- Finish reason: `stop`
- Usage: 21 prompt tokens, 3 completion tokens, 24 total
- Runtime reported total time: 0.29 seconds
- Requested exact text: `ALPHA_OK`
- Observed text: `Alpha_OK.`

The punctuation and case difference is recorded as a small-model instruction-following limitation. It does not satisfy a strict string-equality application assertion, but it does prove non-empty real generation through the complete runtime and broker path.

## Audit and security observations

- The broker returned a generated correlation ID and wrote the matching forwarded event.
- The audit file mode was `0600`.
- Audit records contained method, route, sizes, status, outcome and duration; they did not contain prompt text, model output, caller token or upstream token.
- The product model directory referenced the verified external snapshot; no duplicate model payload was created.

## Remaining gates

- The current link is valid only while the external Hugging Face cache remains present. Startup health must surface a broken or changed external reference and offer recovery.
- Streaming and cancellation still require real-runtime regression coverage.
- This was a terminal-driven engineering regression. A native preflight/install/health/audit user flow is still required before manual Alpha testing.
