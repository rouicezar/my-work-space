# oMLX v0.6.3 native installation recovery evidence

Date: 2026-08-30

Product root: the app's user Application Support directory. No files were installed into `/Applications`.

## Starting state

The first-run operation already had a durable failed state:

- operation ID: `b3b6e7a2-8b2b-43d6-b351-3c4a2cb801b5`
- completed step: `acquire_artifact`
- failed active step: `stage_bundle`
- failure: `STAGED_BUNDLE_INVALID`

The official oMLX DMG remained in the product cache at exactly `807057789` bytes. Its SHA-256 was `5bde65e35c0cc3e7b0365c0e078f98d7571cb71c6a6bead591329a2cf8287537`, matching the pinned manifest. The installation plan therefore reported `cached_artifact_verified: true` and required no network download.

## Defect and repair

An interrupted copy had left an incomplete `.staging-<operation-id>/oMLX.app`. The previous resume behavior revalidated that incomplete directory and failed repeatedly.

The installer now removes only an invalid staging directory owned by the same active operation ID and recopies from the already verified DMG. A failure-first regression creates a partial bundle, interrupts the copy, resumes the same operation, and proves successful activation without changing the operation ID.

## Real recovery result

The Supervisor resumed the existing operation with the exact approved artifact SHA-256. It did not access the network.

- same operation ID retained;
- all three steps completed: `acquire_artifact`, `stage_bundle`, `activate_bundle`;
- final phase: `completed`;
- final revision: `14`;
- active release: `v0.6.3`;
- bundle identifier: `app.omlx`;
- short version: `0.6.3`;
- installed app passed the existing source, staged and final signature/Gatekeeper inspection gates;
- installed app size on the development filesystem: approximately 1.6 GB.

The verified existing Qwen model was then linked into the actual product model directory. That directory consumed 0 bytes of model payload because it contains an external directory link; source ownership remains `external-cache-not-product-owned`.

## Remaining boundary

This proves real installation recovery and activation on the development Mac. It does not yet prove native runtime start/stop, integrated sample inference, byte-level UI progress, clean-machine installation, upgrade, rollback or uninstall.
