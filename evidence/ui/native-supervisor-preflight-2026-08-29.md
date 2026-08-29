# Native Supervisor Preflight UI Evidence

Date: 2026-08-29

Scope: versioned read-only Supervisor protocol consumed by the native SwiftUI prototype.

## Authoritative chain

The development Supervisor called the existing Python preflight implementation rather than reproducing hardware policy in Swift. Its real response used protocol schema 1, echoed the caller UUID and contained an unchanged preflight payload.

Observed on the development Mac:

- architecture: `arm64`
- macOS: `26.6.2`
- measured memory: `19327352832` bytes
- selected provisional profile: `apple-silicon-16gb`
- preflight status: `supported`
- required port 8000: available during the probe

These measurements prove this machine's read-only preflight path only. They are not a multi-machine compatibility claim.

## Protocol and UI checks

- Python command and error paths returned one JSON envelope without tracebacks.
- Swift invoked a direct absolute executable without a shell.
- Swift tests rejected mismatched request IDs, unknown preflight states, structured remote failures and responses above the configured size bound. The decoder also validates command and schema identifiers before accepting a payload.
- When no bundled or explicit development Supervisor exists, the UI shows an unavailable state and does not run a native fallback policy.
- The final ad-hoc signed app bundle launched through macOS Launch Services and visually displayed `Hardware preflight passed`, the provisional profile and the existing lifecycle contract.
- The first screenshots captured only the main display while the app window remained visible on another connected display. Moving the window to the captured display produced the valid inspection. No unnecessary window-placement behavior was retained.

The screenshot was not committed because the surrounding desktop contained unrelated personal content. The temporary app and screenshots are test artifacts, not release deliverables.

## Automated evidence

- Python: 92 tests passed.
- Swift: 14 regular tests passed; the opt-in real temporary Keychain integration test remained skipped in this run.
- Release build, ad-hoc code signature and strict local signature verification passed.

## Remaining Alpha boundary

The self-contained helper packaging gate was subsequently closed by the evidence in `self-contained-supervisor-2026-08-29.md`. Manual Alpha remains blocked until the protocol covers consented installation, progress, cancellation, recovery, model linking, start/stop and post-install deep health.
