# ADR 0005: Resumable and Integrity-Gated Artifact Acquisition

Status: accepted for implementation, 2026-08-29.

## Context

The ordinary-user path must acquire large upstream artifacts without a terminal. oMLX is currently about 807 MB, so interruption, relaunch and insufficient or unstable connectivity are normal states rather than exceptional developer cases. A partially downloaded or redirect-substituted file must never become installable.

## Decision

- Download into the managed cache as `<name>.part`; only an exact size and SHA-256 match permits an atomic rename to the final pinned filename.
- Resume an incomplete file with `Range`. Accept `206` only when `Content-Range` begins at the exact local offset and reports the pinned total size.
- If a server ignores `Range` and returns `200`, truncate and restart rather than append incompatible bytes.
- Retain a genuinely interrupted partial file for retry. Never expose it as an install candidate.
- Reject any transfer that exceeds the pinned size and any final digest mismatch.
- Allow HTTPS redirects only to the reviewed GitHub release hosts. Integrity verification remains mandatory after an allowed redirect.
- Reuse an existing final file only after re-verifying it. An invalid final artifact requires an explicit repair/quarantine operation rather than silent overwrite.
- Flush and `fsync` the partial before verification and atomic publication.

## Remaining integration work

The downloader is a product primitive, not yet the complete installer. The Supervisor must connect progress to the lifecycle journal and UI, enforce disk-space preflight, mount the verified DMG read-only, inspect the contained app again, install into a versioned runtime directory, atomically activate it, and recover or roll back every interrupted step.
