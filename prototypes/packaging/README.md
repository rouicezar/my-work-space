# Packaging Prototypes

This Swift package compares two delivery surfaces against the same product manifest:

- `FormaAIApp`: a minimal SwiftUI management application for the ordinary-user path.
- `forma-ai-launcher`: a headless manifest validator and lifecycle-plan launcher suitable for automation and package scripts.

Neither prototype downloads, installs, starts, updates, or removes upstream software. Health contracts remain unverified. The app can consume the versioned Supervisor preflight protocol when an explicit development helper is provided; it does not reimplement hardware policy in Swift.

## Verify

```bash
swift test --package-path prototypes/packaging
swift run --package-path prototypes/packaging forma-ai-launcher \
  --manifest config/product-manifest.json
swift build --package-path prototypes/packaging --product FormaAIApp
```

The SwiftUI executable proves compilation and shared-contract loading. A later packaging task must create a signed `.app`, verify Gatekeeper behavior, inspect accessibility, and test clean-machine installation before this becomes a release surface.

## Prototype bundles

```bash
./prototypes/packaging/build-app.sh /tmp/forma-ai-app
./prototypes/packaging/build-launcher-pkg.sh /tmp/forma-ai-pkg
```

The app receives an ad-hoc development signature and embeds the exact repository product manifest as a resource. The package is intentionally unsigned: it exists to measure structure and installer behavior, not to impersonate a distributable release. Developer ID signing and notarization remain release gates.

`build-app.sh` freezes the existing Python Supervisor with pinned PyInstaller 6.22.2 and embeds it under `Contents/Helpers/Supervisor`. The end-user app does not require Python. For a repository-only protocol check without packaging, the executable still accepts an explicit absolute `FORMA_AI_SUPERVISOR` development override, but the bundled helper always takes precedence.
