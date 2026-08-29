# ADR 0006: Versioned Runtime Installation and Atomic Activation

Status: accepted for implementation, 2026-08-29.

## Decision

oMLX is installed into a user-owned, versioned product runtime directory. Acquisition, staging and activation are separate journaled steps.

1. Acquire and verify the pinned DMG in managed cache.
2. Mount it read-only and inspect the source application identity, version, architecture, signature and Gatekeeper result.
3. Copy with macOS `ditto` into an operation-specific staging directory on the same filesystem.
4. Inspect the staged copy again; only a valid copy is atomically renamed to the version destination.
5. Re-inspect the installed destination and atomically replace a private `omlx-active.json` pointer.

An existing active record is unchanged until the new bundle has passed every gate. Failed operations keep the same operation ID and resume the same step. Existing invalid final bundles and invalid staging directories fail explicitly and require repair; they are never silently overwritten.

## Boundaries

The implementation currently covers installation transaction semantics. Disk-space reservation, download progress persistence, launch supervision, rollback selection, old-version retention, quarantine repair, uninstall and a real clean-machine install remain separate gates.
