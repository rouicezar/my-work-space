# ADR 0007: Keychain-Backed Runtime Secrets

Status: accepted for implementation, 2026-08-29.

## Decision

- Store the inference-broker caller token and oMLX API key as separate generic-password items in macOS Keychain under service `app.forma-ai.runtime`.
- Generate each from 32 bytes of `SecRandomCopyBytes` and encode it as URL-safe Base64 without padding.
- Use `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`; runtime secrets do not synchronize through iCloud Keychain and are unavailable while the device is locked.
- Reuse valid existing secrets across launches. Invalid or duplicate existing values fail closed rather than being silently replaced.
- Never pass secret values as command-line arguments, persist them in product JSON, include them in descriptions, or emit them into audit and diagnostics.
- Inject values into the child environment only at spawn time. Environment construction and child-process redaction remain separate Supervisor work.
- Delete both items only during an explicitly selected credential-removal/uninstall operation.

## Evidence boundary

The Security.framework implementation and in-memory contract tests compile and pass. A real temporary Keychain integration test, locked-Keychain behavior, access-group/signing configuration, child injection and uninstall confirmation remain required before the Alpha manual test.
