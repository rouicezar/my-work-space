# Self-Contained Supervisor Helper Evidence

Date: 2026-08-29

Scope: freeze the existing Python Supervisor, embed it in the native app and run preflight without an external Python runtime or development environment override.

## Build boundary

- Build tool: PyInstaller `6.22.2`, invoked in an isolated `uv tool run` environment.
- Layout: `onedir`, embedded at `Contents/Helpers/Supervisor`.
- Frozen Python: 3.12.12 supplied by the isolated build environment.
- Target: thin arm64 Mach-O.
- Helper/app size in this build: approximately 20 MB.
- The helper's main executable directly linked only system `libSystem` and `libz`; the Python runtime was present inside the helper directory.

PyInstaller's official documentation describes `onedir` as a folder bundle, documents arm64 targeting and automatic ad-hoc re-signing on Apple Silicon, and warns that `onefile` app bundles unpack on each run and have additional sandbox/notarization limitations. Sources:

- https://pyinstaller.org/en/stable/usage.html
- https://pyinstaller.org/en/stable/feature-notes.html

## Runtime checks

1. The frozen helper ran under an environment containing only the system `PATH` and returned a schema-1, correlated, real preflight response.
2. The complete app launched through macOS Launch Services without `MAC_AI_WORK_OS_SUPERVISOR` or another helper override.
3. The UI displayed `Hardware preflight passed` and the `apple-silicon-16gb` provisional profile, proving the bundled helper was resolved and executed.
4. The helper executable passed strict code-signature verification before embedding.
5. After embedding, the complete app passed deep strict code-signature verification, including the frozen Python library and archive.
6. The SwiftUI window was bounded to 620–800 points wide and 440–700 points high. The final inspected window was 800×675 and displayed every component state without horizontal clipping.

The screenshot was not committed because visual evidence did not require retaining unrelated desktop pixels. The temporary app was not promoted as a release artifact.

## Remaining release gates

- This binary was frozen on macOS 26 and is only development-machine evidence. Release builds must be produced and tested on the oldest supported macOS target.
- The build currently pins PyInstaller itself but does not yet lock every transitive build package by hash.
- Ad-hoc signatures are not Developer ID signatures. Hardened runtime, notarization and Gatekeeper distribution checks remain open.
- The Supervisor currently exposes read-only preflight only. Installation, progress, cancellation, recovery, model linking, lifecycle control and deep health still need versioned commands before manual Alpha.

## Automated regression

- Python: 95 tests passed after adding fail-closed packaging-script checks.
- Swift: 14 regular tests passed; the opt-in real temporary Keychain integration test remained skipped in this run.
- Both packaging shell scripts passed POSIX shell syntax validation.
