# ADR 0010: Self-Contained Supervisor Helper

Status: accepted for Alpha implementation, 2026-08-29.

## Context

The native app now consumes one versioned Supervisor protocol, but the development entry requires an external Python installation. Ordinary users cannot be asked to install Python or set an environment variable. Porting the policy to Swift would reintroduce the duplicate truth source that ADR 0009 prohibits.

## Decision

- Freeze the existing Python Supervisor and its imported product modules as a PyInstaller `onedir` console executable.
- Embed the complete frozen directory at `Contents/Helpers/Supervisor` in the Swift app bundle.
- Resolve the bundled helper before any development override. Public builds must not rely on the override.
- Keep hardware profiles and product manifests as app resources so the app supplies explicit absolute paths through the protocol.
- Build with pinned PyInstaller `6.22.2`, `--clean`, `--noconfirm`, `--onedir`, an explicit repository import path and operation-specific temporary build directories.
- Inspect the output architecture and verify its code signature before embedding. Re-sign and verify the complete app after all helper files and resources are present.
- Refuse to build over an existing app/helper destination so stale frozen files cannot survive into a new artifact.

## Why `onedir`

PyInstaller documents that `onefile` extracts its embedded runtime on every invocation and that onefile macOS app bundles have sandbox/notarization limitations. This Supervisor is called repeatedly and already lives inside a containing app, so a stable embedded directory is more predictable and auditable.

## Compatibility and release boundary

PyInstaller builds for the current platform and architecture. This project's supported target is Apple Silicon, so the Alpha helper is arm64. A binary frozen on the current macOS 26 development machine is single-machine evidence only. Release compatibility must be rebuilt and tested on the oldest supported macOS version, then Developer ID signed, hardened and notarized with the enclosing app.

The build tool is not a runtime dependency. End users receive the frozen helper and do not install Python, PyInstaller or `uv`.
