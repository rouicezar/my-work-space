<div align="center">
  <img src="assets/branding/forma-ai-app-icon-1024.png" alt="Forma AI" width="120" />
</div>

<h1 align="center">Forma AI</h1>

<p align="center"><strong>A local-first, multi-agent AI workbench for the Mac.</strong></p>

<p align="center">
  <a href="README.zh-CN.md">简体中文</a>
</p>

> **Status: in active development.** Forma AI is not yet a finished, distributable product. The links below describe the intended final experience and acceptance standard; they are not evidence that the current build already provides every capability described.

## What is Forma AI?

Forma AI is a general-purpose, distributable AI work operating system for ordinary Mac users. Its product-owned native workbench is the default user entry point. Through a stable adapter protocol it composes the licensed capabilities of four upstream projects — long-term memory, end-to-end audit, parallel multi-agent execution, local-first inference, and permission-gated real tool operations.

## Features

- **Out of the box** — graphical install and initialization with automatic Mac detection, compatible configuration, and health checks.
- **Ordinary-user-first** — day-to-day use never requires understanding MCP, model endpoints, process management, or knowledge graphs.
- **Secure by default** — least privilege, action preview, explicit approval, revocable actions, and full audit.
- **Dual-model, local-first** — local Qwen via oMLX by default; cloud (DeepSeek) only on explicit, per-request approval of a previewed payload.
- **Replaceable components** — the four upstream projects form the default distribution but remain decoupled through stable contracts.
- **Honest degradation** — a component failure is never presented as success, and privacy or execution semantics are never silently changed.

## Components

| Component | Role |
| --- | --- |
| Forma AI native workbench | Default UI for tasks, approvals, status, results, settings, and recovery |
| Herdr | Core multi-agent, terminal, and background-process execution runtime |
| Semantica | Governed long-term knowledge, decision, evidence, and audit authority |
| oMLX | Local model, embedding, and reranking inference on Apple Silicon |
| holaOS | Non-visual capability and workflow reference (reused only behind the adapter boundary) |

## Getting started

> A stable release and its installer are not yet available. The project is currently in active development; the current Mac is the first development and acceptance environment, not the product's sole target.

## Documentation

- [English — Complete Product Overview and User Guide](docs/guides/forma-ai-user-guide.en.md)
- [简体中文 — 完整产品简介与使用指南](docs/guides/forma-ai-user-guide.zh-CN.md)
- [Novice-user acceptance script](docs/runbooks/novice-acceptance.md)

## License

Forma AI's own license is not yet finalized; future public distribution is gated separately. It composes four upstream components, each under its own license: Semantica (MIT), Herdr (Apache-2.0), oMLX (Apache-2.0), and holaOS (modified Apache-2.0, external-install reference only).

## Language

This README is also available in [简体中文](README.zh-CN.md).
