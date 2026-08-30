# Governed memory service contract evidence

Date: 2026-08-30

## Implemented boundary

The product-owned service binds only to literal `127.0.0.1`, requires a
distinct bearer token of at least 32 characters, rejects unlisted routes and
oversized or invalid JSON requests, bounds concurrent work, emits no-store
responses, and writes redacted request-level audit events correlated with the
governance journal.

The versioned operations are `propose`, `confirm`, `reject`, `correct`,
`delete`, `get`, `retrieve`, `history`, `export`, and `health`. Correlation IDs
come from the authenticated request boundary; callers cannot silently place a
different correlation identifier inside mutation payloads.

## Verified behavior

Automated tests exercise a real loopback HTTP socket and prove authentication,
correlation, route and body denial, candidate separation, explicit promotion,
retrieval, correction history, export, deletion, rejection, health, unavailable
Semantica failure, sanitized internal errors, and content-free request audit.

## Remaining boundary

This evidence covers the service contract with a synthetic Semantica backend.
It does not prove Supervisor start/stop, managed-environment installation, a
production embedding route, restart persistence through the HTTP process, or
the native UI workflow. Those remain required before manual memory acceptance.
