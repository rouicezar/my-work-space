# Native oMLX installation-plan evidence

Date: 2026-08-29

Scope: Alpha first-run installation preview and consent boundary. This is not evidence that the full product or clean-machine installation is complete.

## Build and protocol evidence

- Built `Forma AI.app` from the repository with `prototypes/packaging/build-app.sh`.
- Bundle size was 21 MB and deep ad-hoc signature verification passed.
- The bundle contained its self-contained Supervisor helper plus `product-manifest.json`, `hardware-profiles.json`, and `upstreams.json`.
- Calling the bundled helper's read-only `installation-plan` command on macOS 26 returned oMLX `v0.6.3`, artifact size `807057789`, SHA-256 `5bde65e35c0cc3e7b0365c0e078f98d7571cb71c6a6bead591329a2cf8287537`, zero reusable bytes in the isolated check root, and `approval_required: true`.
- The plan check did not start a lifecycle operation, download the artifact, or install a component.

## Visual inspection

The built app was launched on the development Mac. At an approximately 800 by 700 point window, the visible first-run screen showed:

- authoritative hardware preflight success and the provisional 16 GB profile;
- oMLX `v0.6.3` selected by the bundled manifest;
- `807.1 MB` remaining and total download size;
- the user Application Support destination;
- a single prominent `Approve and install oMLX` action;
- lifecycle manifest status and all four component versions.

The content remained readable without clipping, and the screen is scrollable for smaller content heights. No approval button was pressed during this evidence run.

## Automated gates

- 102 Python tests passed.
- 16 Swift tests passed; the opt-in real temporary Keychain test remained skipped in this run.
- Protocol tests cover exact approval-digest matching, stale active-record rejection, honest absent status, unsafe root rejection, structured runtime failure, correlation, and response bounds.

## Remaining boundary

Before this becomes a manual Alpha handoff, the UI still needs a verified real install/resume run, real start and model reuse, a sample inference task, and a user-visible operation progress/recovery experience. Developer ID signing, notarization, clean-machine coverage, upgrade, rollback, and uninstall also remain release work.
