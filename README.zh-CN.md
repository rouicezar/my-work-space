<div align="center">
  <img src="assets/branding/forma-ai-app-icon-1024.png" alt="Forma AI" width="120" />
</div>

<h1 align="center">Forma AI</h1>

<p align="center"><strong>面向 Mac 的本地优先、多 Agent AI 工作台。</strong></p>

<p align="center">
  <a href="README.md">English</a>
</p>

> **状态：正在积极开发中。** Forma AI 尚未成为可分发、已完成的正式产品。下面的链接描述的是目标正式版的最终体验与验收标准，不代表当前开发版本已经具备全部所述能力。

## 什么是 Forma AI？

Forma AI 是一套面向普通 Mac 用户、通用且可分发的 AI 工作操作系统。产品自有原生工作台是默认用户入口；它通过稳定适配协议组合四个上游项目的许可内能力——长期记忆、端到端审计、多 Agent 并行执行、本地优先推理，以及经过权限闸门的真实工具操作。

> 开发状态（2026-09-04）：架构与若干上游适配器切片已有验证，但正式应用首启以及统一的“工作台 → Herdr → 受治理工具 → History”生产链正在纠偏实现中。当前仓库尚未达到发布就绪或真正开箱即用。

## 特性

- **开箱即用** —— 图形化安装与初始化，自动检测 Mac、选择兼容配置并完成健康检查。
- **普通用户优先** —— 日常使用无需理解 MCP、模型端点、进程管理或知识图谱。
- **安全默认** —— 最小权限、操作预览、显式批准、可撤销动作和完整审计。
- **双模型、本地优先** —— 默认通过 oMLX 使用本地 Qwen；只有在预览载荷并逐次批准后才使用云端（DeepSeek）。
- **组件可替换** —— 四个上游项目构成默认发行版，但通过稳定契约解耦。
- **诚实降级** —— 组件故障绝不伪装成成功，也绝不静默改变隐私或执行语义。

## 组件

| 组件 | 职责 |
| --- | --- |
| Forma AI 原生工作台 | 任务、批准、状态、结果、设置与恢复的默认 UI |
| Herdr | 核心多 Agent、终端与后台进程执行运行时 |
| Semantica | 受治理的长期知识、决策、证据与审计权威层 |
| oMLX | Apple Silicon 上的本地模型、Embedding 与 Reranking 推理层 |
| holaOS | 非视觉能力与工作流参考（仅经适配边界复用） |

## 快速开始

> 稳定版本及其安装器尚未发布。项目当前处于积极开发阶段；当前 Mac 是首个开发与验收环境，而非产品的唯一目标。

## 文档

- [简体中文 — 完整产品简介与使用指南](docs/guides/forma-ai-user-guide.zh-CN.md)
- [English — Complete Product Overview and User Guide](docs/guides/forma-ai-user-guide.en.md)
- [新手用户验收脚本](docs/runbooks/novice-acceptance.md)

## 许可证

Forma AI 自身的许可证尚未最终确定；未来公开分发单独把关。它组合四个上游组件，各自遵循自己的许可证：Semantica（MIT）、Herdr（Apache-2.0）、oMLX（Apache-2.0）、holaOS（修改版 Apache-2.0，仅外部安装参考）。

## 语言

本 README 亦有 [English](README.md) 版本。
