# ADR 0002: Native macOS App with Bundled Headless Helper

Status: accepted for product implementation, 2026-08-28.

## Decision

Use a native SwiftUI `.app` as the primary product and ordinary-user interface. Bundle a headless launcher/helper that reads the same product manifest for automation, diagnostics, and lifecycle work. Do not use a standalone `.pkg` launcher as the primary product. Add a signed installer package later only if a proven component requires privileged installation that cannot be safely handled in user space.

## Evidence

The packaging prototype produced and verified both shapes on an Apple Silicon Mac using Swift 6.3.3 and Xcode 26.6:

- Swift package contract tests: 4 passed.
- Python lifecycle and manifest suite at the preceding gate: 24 passed.
- `MacAIWorkOSApp` compiled in release mode.
- A real `.app` bundle was assembled with `Info.plist`, the exact product manifest resource, and the native executable.
- The `.app` passed strict deep ad-hoc `codesign` verification.
- The app launched and visually displayed the four components, pinned versions, correct start order, and explicit unverified health state without installing or starting anything.
- The headless launcher compiled and emitted valid JSON containing the same start/stop plans and non-conflicting ports.
- A prototype `.pkg` containing the launcher was generated and expanded successfully, but it was intentionally unsigned and would install into `/usr/local/bin`, introducing an installer/admin path without delivering the required graphical experience.

These checks prove prototype feasibility, not public distribution readiness. Developer ID signing, notarization, Gatekeeper testing, clean-machine install, accessibility, updater security, and release artifact reproducibility remain open gates.

## Why this shape

### Native app advantages

- Meets the requirement that ordinary users need no terminal.
- Provides one place for preflight, consent, progress, approvals, health, recovery, memory review, and uninstall choices.
- Can use macOS Keychain, accessibility APIs, notifications, background-task controls, code signing, and notarization directly.
- Gives the product one visible lifecycle owner while preserving adapter boundaries.

### Bundled helper advantages

- Supports automated testing, diagnostics, recovery, and advanced operation without duplicating lifecycle policy.
- Can be invoked by the app through a narrow protocol and by developers from a documented path.
- Allows future separation into an XPC service if privilege or isolation requirements are proven.

## Rejected alternatives

- **Standalone `.pkg` plus CLI as the product:** technically simple, but fails the primary no-terminal and ordinary-user requirements and creates an unnecessary administrator-install path.
- **Electron product shell:** overlaps holaOS, adds another large runtime, and does not resolve holaOS redistribution restrictions.
- **Deeply modifying holaOS desktop as our app:** currently blocked by its modified license and would couple the product shell to upstream release cadence.
- **Four independent apps with instructions:** fails unified setup, update, rollback, and honest-health requirements.

## Security and lifecycle consequences

- The app initially operates in user space and stores managed data under the user's Application Support and Cache locations.
- Secrets stay in Keychain.
- The helper must not accept arbitrary shell commands; it will expose versioned lifecycle operations and structured responses.
- Both app and helper validate the same signed product manifest before action.
- Upstream executables remain separate processes with explicit adapters and health contracts.
- Privileged helpers or system extensions require a new threat model and ADR before introduction.

## Remaining release gates

1. Establish final bundle identifier, product name, icons, entitlements, and privacy declarations.
2. Obtain Developer ID Application and Installer identities where required.
3. Sign every nested executable, generate a notarized release artifact, and test Gatekeeper on a clean Mac.
4. Implement secure update ownership and rollback; ad-hoc signing is development-only.
5. Test keyboard navigation, VoiceOver labels, reduced-motion behavior, localization, and error-state clarity.
6. Resolve holaOS licensing before representing it as bundled inside the app.
