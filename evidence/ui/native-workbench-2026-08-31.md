# Native workbench evidence — 2026-08-31

## Accepted boundary

The default user experience is now a product-owned native macOS workbench. Its visual
direction is a restrained, conversation-centered AI workspace inspired by Codex and
comparable AI operating systems without copying proprietary assets. holaOS and Herdr
remain optional replaceable adapters and are not bundled into the primary UI.

## Implemented slice

- Ordinary launch opens `New task`, not the setup assistant.
- The sidebar separates new work, history, and Settings & Recovery.
- The task composer submits through the versioned `task-submit` Supervisor protocol.
- Results distinguish local completion, an offline cloud approval proposal, honest
  capability unavailability, and safe failure.
- Cloud proposal copy states that no data has left the Mac and exposes data classes,
  processing location, model, maximum cost, and audit correlation.
- Installation, model, runtime, component, and recovery details remain in Settings.

## Verification

- Python suite: `224` passed, `1` environment-gated test skipped.
- Swift package: `29` passed, `2` environment-gated tests skipped.
- Release-mode app bundle built and passed strict deep ad-hoc signature verification.
- The packaged app originally launched a process without a window. Root cause was the
  hand-authored bundle metadata missing `NSPrincipalClass=NSApplication`; the metadata
  and a regression test were added, after which the window server reported real app
  windows.
- Direct window capture at the minimum `900 x 732` layout was visually inspected for
  hierarchy, clipping, empty state, composer, privacy copy, route status, sidebar, and
  setup separation: [native-workbench-empty-2026-08-31.png](native-workbench-empty-2026-08-31.png).

## Remaining boundary

This is the first daily-workbench slice, not final usability acceptance. Task history
persistence, task cancellation, cloud credential setup and approval execution UI,
dark-mode and keyboard/accessibility inspection, visual checks of every result state,
and an unfamiliar-user test remain open. A real approved DeepSeek request also remains
an independent release gate.
