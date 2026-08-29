# Packaging Prototypes

This Swift package compares two delivery surfaces against the same product manifest:

- `MacAIWorkOSApp`: a minimal SwiftUI management application for the ordinary-user path.
- `mac-ai-work-os-launcher`: a headless manifest validator and lifecycle-plan launcher suitable for automation and package scripts.

Neither prototype downloads, installs, starts, updates, or removes upstream software. Health contracts remain unverified. The app can consume the versioned Supervisor preflight protocol when an explicit development helper is provided; it does not reimplement hardware policy in Swift.

## Verify

```bash
swift test --package-path prototypes/packaging
swift run --package-path prototypes/packaging mac-ai-work-os-launcher \
  --manifest config/product-manifest.json
swift build --package-path prototypes/packaging --product MacAIWorkOSApp
```

The SwiftUI executable proves compilation and shared-contract loading. A later packaging task must create a signed `.app`, verify Gatekeeper behavior, inspect accessibility, and test clean-machine installation before this becomes a release surface.

## Prototype bundles

```bash
./prototypes/packaging/build-app.sh /tmp/mac-ai-work-os-app
./prototypes/packaging/build-launcher-pkg.sh /tmp/mac-ai-work-os-pkg
```

The app receives an ad-hoc development signature and embeds the exact repository product manifest as a resource. The package is intentionally unsigned: it exists to measure structure and installer behavior, not to impersonate a distributable release. Developer ID signing and notarization remain release gates.

For a repository-only protocol check, launch the built executable with `MAC_AI_WORK_OS_SUPERVISOR` set to the absolute `scripts/supervisor.py` path. Public Alpha builds must instead bundle a self-contained signed helper; they must not depend on a developer Python installation or this environment override.
