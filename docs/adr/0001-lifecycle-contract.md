# ADR 0001: Product-Owned Lifecycle Contract

Status: accepted for prototype implementation, 2026-08-28.

## Context

The four upstream projects have different packaging, runtimes, ports, update systems, data locations, and redistribution constraints. Treating them as four independent installs would expose this complexity to ordinary users and make rollback, audit, and honest health impossible. Deeply rebundling all four is also currently unsafe because holaOS is not cleared for embedded public distribution and oMLX ships a large, specialized runtime.

## Decision

Use a product-owned lifecycle supervisor driven by `config/product-manifest.json`.

- oMLX starts first on product-assigned port `8000`.
- Semantica v0.6.7 is installed second as an isolated Python library. Its
  upstream REST server is not part of the product runtime: it fixes its port at
  `8000`, collides with oMLX, and its `/health` route only proves the web process
  is alive.
- A product-owned, authenticated, loopback-only governed-memory service will
  expose the versioned memory contract on port `43111`. It loads the pinned
  Semantica library and remains unavailable until a separately approved local
  embedding route passes a real probe.
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

The oMLX lifecycle can install and control its reviewed artifact, while the
Semantica managed-environment installer and governed-memory service remain
incomplete. Component health contracts remain explicitly
`pending-adapter-verification`. A Semantica package import or upstream
`/health` response cannot promote memory health; real governed store,
retrieval, restart, and embedding-route evidence are required.

## Consequences

The product can resume interrupted operations without repeating completed steps and can report failures honestly. The manifest gives the future GUI one stable contract. The cost is that adapters must translate product policy into four different upstream mechanisms, and holaOS cannot yet participate in a single bundled release.

## Rejected alternatives

- **Four independent installers:** easy initially, but violates the ordinary-user, rollback, and coordinated-update requirements.
- **One shared Python/runtime environment:** conflicts with Semantica's broad dependencies and oMLX's tightly pinned inference stack.
- **Immediate deep fork and rebundle:** creates maintenance and licensing risk before interface gaps are proven.
- **Allow upstream self-updates:** breaks reproducibility and may silently change APIs or license terms.
