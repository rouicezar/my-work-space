# ADR 0008: Zero-Copy Reference to Existing Model Caches

Status: accepted for implementation, 2026-08-29.

## Context

Users may already have large MLX models in the Hugging Face content-addressed cache. Re-downloading or copying the same weights wastes bandwidth and disk, while treating an external cache as product-owned risks deleting another application's data.

## Decision

- The product model catalog pins repository, immutable 40-character revision, license metadata, model type, architecture, quantization and exact size/SHA-256 for every required file.
- Before reuse, resolve every snapshot entry and prove it remains inside that repository's cache root, is a regular file, and matches the catalog.
- Create an atomic directory symlink under the product-owned oMLX model tree. Do not copy or modify the source snapshot or blobs.
- Persist a private machine-local reference record labeled `external-cache-not-product-owned`.
- A conflicting product path, escaping symlink, missing file, changed digest or incompatible config fails closed.
- Uninstall and unlink operations may remove the product symlink and record only. They must never delete external cache content.
- If the external cache is later evicted, health must report the model reference as broken and offer relink or a separately consented managed download.

## Alpha candidate

The first candidate is `mlx-community/Qwen3-0.6B-4bit` at revision `73e3e38d981303bc594367cd910ea6eb48349da8`, approximately 351 MB in its published repository and Apache-2.0 according to the upstream model records. Its inclusion remains an Alpha compatibility claim only after real pinned-oMLX generation passes.
