# Native existing-model plan and zero-copy reference evidence

Date: 2026-08-30

Scope: Supervisor and native first-run support for reusing a pinned model already present in the standard Hugging Face cache. This is not full Alpha acceptance evidence.

## Real existing-cache verification

The Supervisor ran `model-plan` against the machine's existing Hugging Face cache and the bundled product model catalog. It verified `mlx-community/Qwen3-0.6B-4bit` at immutable revision `73e3e38d981303bc594367cd910ea6eb48349da8`.

Observed authoritative plan fields:

- `available_verified: true`
- `approval_required: true`
- catalogued size: `351383618` bytes
- license: `Apache-2.0`
- quantization: 4-bit
- no unavailable reason

The verification covers all nine pinned files by exact byte size and SHA-256 and checks model type, architecture and quantization metadata through the existing model implementation.

## Real isolated link

After echoing the exact approved revision, `link-model` created a reference under a new temporary product root.

- The model entry was a directory symbolic link to the verified cache snapshot.
- The product root consumed 4 KB; no model weight was copied.
- The state record was mode `0600`.
- The record declared `storage_mode: external-reference` and `source_ownership: external-cache-not-product-owned`.
- No network request occurred and the source cache was not modified.

## UI contract

The native setup assistant now distinguishes a verified existing model from an unavailable cache. It shows repository, catalogued size, license, quantization, revision and the external-ownership warning. It creates the reference only after the user selects `Approve existing model reference`.

The complete app was rebuilt with its self-contained Supervisor and `models.json` resource. Deep ad-hoc signature verification passed, and the bundled helper returned the same verified real-model plan. A window-specific screenshot at 800 by 671 points confirmed that the model details, external-ownership warning and approval action were visible without clipping; remaining manifest content was reachable through the scroll view.

This visual inspection also exposed an ambiguous `Zero KB remaining` installer-cache label. The plan contract was corrected so a complete cached DMG is reusable only after exact size and SHA-256 verification. A verified file now renders as `Verified installer cached · no download required`; an invalid complete file becomes an explicit repair blocker.

## Remaining boundary

A complete Alpha still requires real oMLX installation/resume, runtime start, sample inference, visible operation progress/recovery, and integrated audit evidence.
