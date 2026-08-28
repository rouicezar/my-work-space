# Project Agent Instructions

## Product scope

Build a general-purpose, distributable, out-of-the-box Mac AI Work OS based on Semantica, holaOS, Herdr, and oMLX. The current machine is the first development environment, not the product's sole target or a source of product-specific assumptions.

## Workflow

Follow `requirements → design → implementation → testing → commit → push`.

- Do not implement before requirements and design are accepted.
- Prefer minimal, reversible changes and stable public contracts.
- Test every implementation change and verify the user-visible workflow.
- Keep facts, assumptions, hypotheses, predictions, and opinions distinct.
- Distribution, upgrade, uninstall, documentation, and novice-user evidence are required product work.

## Development isolation

Do not use developer-specific data as a product dependency or modify MyNote, GBrain, existing automations, persistent agent memory, or production accounts without a separately approved connector or migration task. Use repository-local fixtures, test accounts, temporary databases, and synthetic data. Never commit secrets, personal paths in shipped configuration, or machine-specific credentials.

## Component roles

- holaOS is the default user-facing control plane.
- Herdr is the optional advanced multi-agent and terminal console.
- Semantica is authoritative for governed long-term knowledge and decision evidence.
- oMLX is the default local inference layer.
- Product-owned orchestration, policy, lifecycle, and health layers integrate them.

External writes, destructive actions, credential use, and cloud escalation require explicit policy, preview, approval, and audit behavior. Releases must pass clean-install, upgrade, rollback, uninstall, recovery, security, accessibility/usability, and novice-user gates on supported hardware tiers.
