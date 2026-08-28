# ADR 0001: Product-Owned Lifecycle Contract

Status: accepted for prototype implementation, 2026-08-28.

## Context

The four upstream projects have different packaging, runtimes, ports, update systems, data locations, and redistribution constraints. Treating them as four independent installs would expose this complexity to ordinary users and make rollback, audit, and honest health impossible. Deeply rebundling all four is also currently unsafe because holaOS is not cleared for embedded public distribution and oMLX ships a large, specialized runtime.

## Decision

Use a product-owned lifecycle supervisor driven by `config/product-manifest.json`.

- oMLX starts first on product-assigned port `8000`.
- Semantica starts second on proposed port `8765`; the adapter must prove the override before its health contract can be promoted.
- Herdr starts third as the advanced process runtime.
- A separately installed holaOS instance connects last until its distribution license is cleared.
- Stop order is the reverse of start order.
- Semantica and oMLX use separate runtimes and data directories.
- Configuration, state, data, runtimes, logs, backups, cache, and secrets are distinct storage classes.
- Secrets use macOS Keychain.
- Every upstream update passes the product compatibility gate; component self-update is disabled or detected as a blocking drift.
- Install, repair, update, and uninstall are journaled operations with atomic state snapshots and append-only correlated events.
- Uninstall cannot begin without an explicit `keep`, `export`, or `delete` data policy.

## Prototype boundaries

The current lifecycle code persists and validates state only. It does not download, install, start, stop, update, or delete upstream software. Component health contracts remain explicitly `pending-adapter-verification`. Port configurability, updater control, artifact signatures, data paths, and process behavior must be proven by adapter tests before any installation step becomes real.

## Consequences

The product can resume interrupted operations without repeating completed steps and can report failures honestly. The manifest gives the future GUI one stable contract. The cost is that adapters must translate product policy into four different upstream mechanisms, and holaOS cannot yet participate in a single bundled release.

## Rejected alternatives

- **Four independent installers:** easy initially, but violates the ordinary-user, rollback, and coordinated-update requirements.
- **One shared Python/runtime environment:** conflicts with Semantica's broad dependencies and oMLX's tightly pinned inference stack.
- **Immediate deep fork and rebundle:** creates maintenance and licensing risk before interface gaps are proven.
- **Allow upstream self-updates:** breaks reproducibility and may silently change APIs or license terms.
