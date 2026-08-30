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
- Settings accepts a user-provided DeepSeek credential only through a secure field,
  stores it in Keychain, and separately persists explicit cloud enablement. Disablement
  revokes future routing and removes the credential without deleting audit history.
- Proposal approval binds the displayed maximum cost, then executes only the saved
  proposal through the existing one-shot protocol. Rejection removes the pending
  payload. Execution displays normalized output, actual cost, model, and correlation.
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

This is an integrated daily-workbench slice, not final usability acceptance. Task
history persistence, task cancellation, dark-mode and keyboard/accessibility
inspection, visual checks of every result state, and an unfamiliar-user test remain
open. The cloud UI is implemented against synthetic protocol evidence; a real approved
DeepSeek request remains an independent release gate and has not been performed.
