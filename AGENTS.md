# Project Agent Instructions

## Scope

This repository is an isolated sandbox for integrating Semantica, holaOS, Herdr, and oMLX on one personal Mac.

## Workflow

All work follows:

`requirements → design → implementation → testing → commit → push`

- Do not implement before requirements and design are accepted.
- Prefer minimal, reversible changes.
- Every implementation change requires proportionate tests.
- Do not claim completion from process health alone; verify the user-visible workflow.
- Keep evidence, assumptions, and hypotheses explicitly separated.

## Isolation boundary

Until a separate migration project is explicitly approved, do not connect to or modify:

- `/Users/rouice/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyNote`
- `/Users/rouice/Gbrain`
- existing scheduled automations or agent memory
- production email, calendar, Feishu, or other real accounts

Use project-local configuration, databases, fixtures, test accounts, and synthetic data only. Never store secrets in Git.

## Product roles

- holaOS is the default user-facing control plane.
- Herdr is the advanced multi-agent and terminal process console.
- Semantica is the authoritative long-term knowledge and audit layer.
- oMLX is the default local inference layer.

## External writes

File writes outside this repository, real-account actions, destructive operations, and cloud-model escalation require an explicit gate and an audit record.
