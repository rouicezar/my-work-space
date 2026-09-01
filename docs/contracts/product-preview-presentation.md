# Forma AI Product Preview Presentation Contract v1

Status: accepted presentation specification for frontend preview implementation. This contract defines visible final-product scenarios; it does not claim runtime capability.

## 1. Purpose

Product Preview lets the user manually inspect the intended final Forma AI shape before every upstream integration is complete. It is a product-design instrument, not a substitute backend, demo of real execution, or acceptance artifact for Herdr, holaOS, Semantica, oMLX, connectors, cloud providers, Keychain, installation, or recovery.

## 2. Authority boundary

The preview provider owns no runtime state. It may represent only presentation data derived from the documented shapes of:

- Herdr agent, pane, task-lifecycle, event, and artifact surfaces;
- holaOS workflow/application/tool capability declarations;
- Semantica candidate/confirmed/conflict/correction presentation needs;
- oMLX and approved-cloud model/route states;
- Forma AI permission, approval, audit, lifecycle, and native-navigation contracts.

If a future upstream response cannot map to this presentation contract without changing its semantics, the contract and UI must change. Forma AI must not add a competing runtime to preserve an obsolete preview.

## 3. Hard isolation rules

Preview mode must:

- be explicitly selected through a development-only launch configuration;
- show `Product Preview · synthetic data · no runtime action` persistently;
- use deterministic repository-defined scenarios;
- remain in memory and write no product data;
- make no Supervisor, adapter, process, socket, network, filesystem mutation, connector, Keychain, notification, or cloud call;
- expose no real local paths, accounts, prompts, credentials, or user content;
- use synthetic IDs prefixed with `preview-`;
- never be selected automatically after runtime failure;
- never satisfy a runtime, integration, security, recovery, or release acceptance test.

Release builds omit or disable Product Preview unless a separately approved demo-mode decision provides a user purpose, security review, and permanent support contract.

## 4. Presentation model

The preview provider exposes one immutable `ProductPreviewScenario`:

| Field | Requirement |
|---|---|
| `schemaVersion` | Exactly `1` |
| `scenarioID` | Stable `preview-*` identifier |
| `title` | Human-readable scenario name |
| `summary` | One-sentence purpose |
| `activeDestination` | New task, History, or Settings |
| `task` | Optional read-only task presentation |
| `history` | Bounded synthetic task summaries |
| `settings` | Synthetic capability and policy summaries |
| `notice` | Mandatory preview disclosure |

A task presentation may contain goal, route, state, correlation label, steps, agents, approvals, artifacts, validation results, final result, and unresolved items. These are display values, not executable commands.

## 5. Required scenarios

1. `preview-empty-workbench` — new task, no user data.
2. `preview-local-complete` — one local task with evidence and validation.
3. `preview-parallel-blocked` — three Herdr-shaped Agent cards, one awaiting a scoped approval.
4. `preview-partial-evidence` — valid artifacts plus unresolved evidence and no false completion.
5. `preview-cloud-proposal` — exact one-time proposal before transmission.
6. `preview-interrupted-recovery` — interrupted task with reconciled-resume and explicit fresh-run choices shown as presentation only.
7. `preview-memory-governance` — candidate, confirmed, conflict, correction, and delete states.
8. `preview-component-unavailable` — honest missing capability and recovery guidance.

## 6. Action behavior

Preview controls may do only one of the following:

- navigate between preview surfaces;
- expand or collapse details;
- switch to another deterministic preview scenario;
- change an ephemeral presentation selection;
- copy synthetic text explicitly marked as sample content.

Buttons whose runtime meaning would be approve, send, delete, execute, cancel, resume, install, start, stop, repair, export, open artifact, save credential, or revoke must be disabled or converted into `Show next preview state`. The UI must never use the exact production action label on an inert control without a nearby preview explanation.

## 7. Runtime separation

Runtime mode and preview mode use different providers behind the same read-only presentation protocol:

- `ProductPreviewProvider` returns immutable synthetic presentation data.
- `RuntimePresentationProvider` maps authoritative adapter and policy responses.

Neither provider exposes execution methods. Production actions remain separate command clients with policy and approval gates. This prevents a view model or preview fixture from becoming an accidental runtime state machine.

Runtime provider failure renders an honest unavailable/unknown state. It must never fall back to `ProductPreviewProvider`.

## 8. Accessibility and visual requirements

- The preview disclosure is available to VoiceOver and not conveyed only by color.
- Every state has text and symbol semantics.
- Keyboard navigation reaches all destinations and expandable details.
- Layout works at the supported minimum window and common larger sizes.
- Text scaling does not hide state, approval scope, unresolved items, or preview disclosure.
- Light and dark appearances preserve hierarchy and contrast.
- Animation respects Reduce Motion.

## 9. Verification

P4-T11 implementation must prove:

1. all eight scenarios are reachable;
2. every ID uses the `preview-` prefix;
3. the mandatory disclosure is always visible and accessible;
4. the provider has no dependency on command clients, Keychain, network, filesystem mutation, or adapters;
5. runtime failure never selects preview data;
6. production initializers default to runtime mode;
7. Swift baseline remains green.

Screenshots may prove layout and visible disclosure only. They do not prove upstream execution.
