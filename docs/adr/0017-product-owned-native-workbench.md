# ADR-0017: Product-owned native workbench

Status: accepted, 2026-08-30.

## Context

The product needs a stable ordinary-user interface that can be distributed, secured,
tested, and evolved independently. holaOS remains useful as an interaction adapter,
but its current redistribution boundary does not support making an embedded holaOS UI
a mandatory product dependency. The existing SwiftUI surface is a setup prototype and
does not yet provide a daily task experience.

## Decision

1. The first distributable product uses a product-owned native macOS workbench.
2. Its visual direction is a restrained, conversation-centered AI workspace inspired
   by Codex and comparable AI operating systems without copying proprietary assets.
3. Ordinary launch opens tasks, history, approvals, and simple status. Installation,
   model details, component names, ports, and diagnostics live in Settings & Recovery.
4. Task state exposes only honest user-facing routes: completed locally, approval
   required with no transmission, or unavailable with a recovery action.
5. holaOS remains a replaceable optional adapter behind a versioned contract. It does
   not own lifecycle, policy, audit, memory authority, or the default distribution UI.
6. Herdr remains the optional advanced multi-agent and process console.

## Required evidence

- Native compile and protocol tests.
- Local, proposal, unavailable, loading, empty, and failure visual states.
- Keyboard submission, accessible labels, window resizing, light/dark appearance, and
  separation between daily workbench and setup/recovery.
- No personal paths, credentials, prompts, or results in shipped resources or logs.
