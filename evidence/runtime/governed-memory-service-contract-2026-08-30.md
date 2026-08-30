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

The RuntimeManager contract starts the service after oMLX and the inference
broker, stops it before both, degrades status when its recorded process identity
is missing, and cleans up all started processes on a memory-service timeout.
A real Supervisor child-process test verifies authenticated liveness, honest
unavailable health, candidate persistence across restart, and redacted audit.

## Remaining boundary

This evidence covers a real service process with an intentionally unavailable
Semantica backend and a synthetic three-process lifecycle controller. It does
not prove the full real oMLX + broker + memory process sequence,
managed-environment installation, a production embedding route, confirmed
memory across process restart, or the native UI memory workflow. Those remain
required before manual memory acceptance.
