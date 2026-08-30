# Forma AI

![Forma AI app icon](assets/branding/forma-ai-app-icon-1024.png)

Forma AI 是一套面向普通 Mac 用户、通用且可分发的 AI 工作操作系统。它组合 Semantica、holaOS、Herdr 与 oMLX，提供统一入口、长期记忆、端到端审计、多 Agent 并行、本地优先推理，以及经过权限闸门的真实工具操作。

目标不是让四个上游项目“同时启动”，而是把它们产品化为一套开箱即用、部署简单、操作方便、安全可恢复的完整系统。

## 产品原则

- **开箱即用**：图形化安装和初始化，自动检测 Mac、选择兼容配置并完成健康检查。
- **普通用户优先**：日常使用无需理解 MCP、模型端点、进程管理或知识图谱。
- **安全默认**：最小权限、操作预览、显式批准、可撤销动作和完整审计。
- **双模型、本地优先**：默认通过 oMLX 使用本地 Qwen；只有在本地能力边界明确且用户逐次批准后，才向可关闭、可替换的 DeepSeek 云端路径发送经过预览的数据。
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
- [产品架构设计](docs/plans/2026-08-28-forma-ai-design.md)
- [产品实施计划](docs/plans/2026-08-28-forma-ai.md)
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
- [已有模型零复制引用 ADR](docs/adr/0008-zero-copy-model-reference.md)
- [Supervisor 与原生 App 协议 ADR](docs/adr/0009-supervisor-app-protocol.md)
- [自包含 Supervisor Helper ADR](docs/adr/0010-self-contained-supervisor-helper.md)
- [私密本地任务协议 ADR](docs/adr/0015-private-local-task-protocol.md)
- [统一任务路由状态 ADR](docs/adr/0016-unified-task-routing-state.md)
- [Swift 打包原型](prototypes/packaging/README.md)
- [oMLX 适配器运行手册](docs/runbooks/omlx.md)
- [Semantica 受管运行环境手册](docs/runbooks/semantica.md)
- [oMLX v0.6.3 实测证据](evidence/upstream/omlx-v0.6.3-macos26-2026-08-29.md)
- [oMLX 隔离与真实代理回归证据](evidence/upstream/omlx-v0.6.3-isolation-broker-2026-08-29.md)
- [现有 Qwen 模型零复制与真实生成证据](evidence/upstream/omlx-v0.6.3-qwen3-generation-2026-08-29.md)
- [Semantica v0.6.7 治理记忆契约证据](evidence/upstream/semantica-v0.6.7-governed-memory-contract-2026-08-30.md)
- [受治理记忆服务契约证据](evidence/runtime/governed-memory-service-contract-2026-08-30.md)
- [双模型 Supervisor 协议证据](evidence/runtime/dual-model-supervisor-protocol-2026-08-30.md)
- [私密本地 Qwen 日常任务证据](evidence/runtime/private-local-task-2026-08-30.md)
- [oMLX v0.6.3 Embedding 能力边界证据](evidence/upstream/omlx-v0.6.3-embedding-capability-2026-08-30.md)
- [原生 Supervisor 预检界面证据](evidence/ui/native-supervisor-preflight-2026-08-29.md)
- [自包含 Supervisor Helper 证据](evidence/ui/self-contained-supervisor-2026-08-29.md)

## 开发者预检

当前阶段可运行只读环境检测：

```bash
./scripts/preflight.sh
```

它输出机器可读 JSON，并明确区分 `supported`、`unknown` 和 `unsupported`。当前配置阈值仍是暂定值，不代表正式兼容性承诺。

只有当安装、初始化、核心工作流、安全、审计、恢复、升级、卸载、文档和陌生用户验收全部有直接证据时，才能宣布产品阶段完成。
