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
5. holaOS does not own the default distribution UI, but its licensed non-visual
   workflow and application capabilities are reused through a versioned integration
   boundary wherever compatible. Visual assets, branding, and public bundling are
   reviewed separately.
6. Herdr is the required core multi-agent execution runtime. Its terminal and process
   console may be hidden from ordinary users, but parallel execution, status,
   cancellation, resume, recovery, and handoff must use or extend Herdr rather than
   reimplementing an independent competing runtime.
7. Before product-owned implementation of a non-visual capability, record whether it
   already exists in Semantica, holaOS, Herdr, or oMLX and why direct reuse or a thin
   adapter is or is not viable.

## Required evidence

- Native compile and protocol tests.
- Local, proposal, unavailable, loading, empty, and failure visual states.
- Keyboard submission, accessible labels, window resizing, light/dark appearance, and
  separation between daily workbench and setup/recovery.
- No personal paths, credentials, prompts, or results in shipped resources or logs.
