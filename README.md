# Mac AI Work OS

Mac AI Work OS 是一套面向普通 Mac 用户、通用且可分发的 AI 工作操作系统。它组合 Semantica、holaOS、Herdr 与 oMLX，提供统一入口、长期记忆、端到端审计、多 Agent 并行、本地优先推理，以及经过权限闸门的真实工具操作。

目标不是让四个上游项目“同时启动”，而是把它们产品化为一套开箱即用、部署简单、操作方便、安全可恢复的完整系统。

## 产品原则

- **开箱即用**：图形化安装和初始化，自动检测 Mac、选择兼容配置并完成健康检查。
- **普通用户优先**：日常使用无需理解 MCP、模型端点、进程管理或知识图谱。
- **安全默认**：最小权限、操作预览、显式批准、可撤销动作和完整审计。
- **本地优先**：默认使用本地推理；联网和云模型路径必须可见、可控、可关闭。
- **组件可替换**：四个项目构成默认发行版，但通过稳定契约解耦。
- **诚实降级**：组件故障不得伪装成成功，也不得静默改变隐私或执行语义。

## 默认组件职责

| 组件 | 产品职责 |
|---|---|
| holaOS | 普通用户的统一图形入口、应用连接与任务交互 |
| Herdr | 高级模式下的多 Agent、终端和后台进程控制台 |
| Semantica | 经过治理的长期知识、决策、证据与审计权威层 |
| oMLX | Apple Silicon 上的本地模型、Embedding 与 Reranking 推理层 |

当前 Mac 仅作为首个开发与验收环境，不是产品的唯一目标用户。

- [产品需求](docs/product-requirements.md)
- [产品架构设计](docs/plans/2026-08-28-mac-ai-work-os-design.md)
- [产品实施计划](docs/plans/2026-08-28-mac-ai-work-os.md)
- [架构决策记录](docs/decisions.md)
- [暂定 Mac 支持矩阵](docs/support-matrix.md)
- [上游兼容性矩阵](docs/research/upstream-matrix.md)
- [上游许可证与分发矩阵](docs/research/license-matrix.md)
- [生命周期契约 ADR](docs/adr/0001-lifecycle-contract.md)
- [macOS 打包架构 ADR](docs/adr/0002-packaging-architecture.md)
- [oMLX 进程安全边界 ADR](docs/adr/0003-omlx-process-security-boundary.md)
- [本地推理代理 ADR](docs/adr/0004-local-inference-broker.md)
- [可续传构件获取 ADR](docs/adr/0005-resumable-artifact-acquisition.md)
- [版本化运行时安装 ADR](docs/adr/0006-versioned-runtime-installation.md)
- [Keychain 运行时密钥 ADR](docs/adr/0007-keychain-runtime-secrets.md)
- [Swift 打包原型](prototypes/packaging/README.md)
- [oMLX 适配器运行手册](docs/runbooks/omlx.md)
- [oMLX v0.6.3 实测证据](evidence/upstream/omlx-v0.6.3-macos26-2026-08-29.md)
- [oMLX 隔离与真实代理回归证据](evidence/upstream/omlx-v0.6.3-isolation-broker-2026-08-29.md)

## 开发者预检

当前阶段可运行只读环境检测：

```bash
./scripts/preflight.sh
```

它输出机器可读 JSON，并明确区分 `supported`、`unknown` 和 `unsupported`。当前配置阈值仍是暂定值，不代表正式兼容性承诺。

只有当安装、初始化、核心工作流、安全、审计、恢复、升级、卸载、文档和陌生用户验收全部有直接证据时，才能宣布产品阶段完成。
