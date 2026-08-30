# ADR-0016: Unified task routing state

Status: accepted, 2026-08-30.

## Context

The product now has separately tested local-task and cloud-proposal protocols. A daily
workbench still cannot choose between them safely unless product-owned state answers:

- which local model profile was actually verified, and on what evidence;
- whether the local runtime is healthy now;
- whether the optional cloud route is enabled by this user;
- which provider/model the user selected; and
- whether current task requirements fit the local and cloud contracts.

None of those decisions may be delegated to model self-assessment or hidden UI logic.

## Decision

1. Add a strict, versioned local-capability catalog. A profile binds the product model
   definition, tested capabilities, context and output ceilings, minimum available
   memory, validation policy, evidence path, and evidence status.
2. Treat single-machine evidence honestly. The initial Qwen profile exposes only the
   short-text context and output ceiling already proven by the real local-task run and
   is `verified_single_machine`, not a general benchmark claim. Larger local boundaries
   require a separate real benchmark before the catalog may expand them.
3. Store cloud preferences separately from credentials. Missing state means disabled.
   Enabling records only provider/model selection; the API key remains in Keychain.
4. Cloud preference files are product-owned private state. Unknown fields, unsafe
   paths, unsupported providers/models, or malformed state fail closed to disabled.
5. A unified task submission derives current local health and resource evidence inside
   Supervisor, loads these catalogs, then makes one deterministic routing decision.
6. A local decision executes only the local task protocol. An ineligible decision may
   create an offline cloud proposal only when cloud is enabled and the selected cloud
   model satisfies the task. It never transmits.
7. When cloud is disabled, unavailable, stale, or incompatible, return a visible
   `capability_unavailable` state with local reason codes. Do not silently relax task
   requirements or choose another provider.
8. Local result validation failure is a new routing event. The user sees the failed
   validation and may receive an offline proposal; the local result is never relabeled
   as a cloud-quality success.

## Required evidence

- Strict valid/invalid local-profile and cloud-preference contract tests.
- Default-disabled, explicit enable, disable, restart persistence, and corrupted-state
  recovery tests.
- Local eligible, every local-ineligible reason, disabled-cloud, stale-price, blocked
  data class, approved cloud, and local-validation-failure task journeys.
- Audit correlation across plan, local execution, proposal, decision, cloud execution,
  result, failure, and recovery without prompt/result bodies.
