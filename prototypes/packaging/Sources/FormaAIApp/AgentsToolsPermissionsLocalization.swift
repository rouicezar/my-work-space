import LifecycleContract

enum AgentsToolsCopyKey {
    case agentsToolsTitle, agentsToolsSyntheticOnly, agentsToolsPreviewBadge
    case requiredOperations, agentsAuthorityBoundary, agentsAuthorityBoundaryBody
}

enum PermissionsCopyKey {
    case permissionsTitle, permissionsSyntheticOnly, permissionsPreviewBadge
    case approvalPolicy, permissionsAuthorityBoundary, permissionsAuthorityBoundaryBody
}

extension ProductCopy {
    subscript(key: AgentsToolsCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .agentsToolsTitle): "Agents 与工具"
        case (.simplifiedChinese, .agentsToolsSyntheticOnly): "4 个合成适配器样例，用于检查最终产品如何呈现 Agent 适配范围与必需操作。"
        case (.simplifiedChinese, .agentsToolsPreviewBadge): "预览样例"
        case (.simplifiedChinese, .requiredOperations): "必需操作"
        case (.simplifiedChinese, .agentsAuthorityBoundary): "执行权威边界"
        case (.simplifiedChinese, .agentsAuthorityBoundaryBody):
            "Herdr 是唯一的 Agent 执行权威；适配器只把 vendor-neutral 契约翻译到具体工具，"
            + "绝不重建执行状态机。holaOS 仅作为外部安装参考展示其工作流/工具能力。"
        case (.english, .agentsToolsTitle): "Agents & Tools"
        case (.english, .agentsToolsSyntheticOnly): "Four synthetic adapter examples for reviewing how the finished product presents agent adapter scope and required operations."
        case (.english, .agentsToolsPreviewBadge): "PREVIEW EXAMPLE"
        case (.english, .requiredOperations): "Required operations"
        case (.english, .agentsAuthorityBoundary): "Execution authority boundary"
        case (.english, .agentsAuthorityBoundaryBody):
            "Herdr is the sole agent execution authority; adapters translate the vendor-neutral "
            + "contract to a specific tool and never rebuild an execution state machine. "
            + "holaOS is shown only as an external-install reference for workflow/tool capabilities."
        }
    }

    subscript(key: PermissionsCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .permissionsTitle): "权限与审批"
        case (.simplifiedChinese, .permissionsSyntheticOnly): "6 个合成权限范围样例，用于检查最终产品如何呈现权限范围与审批策略。"
        case (.simplifiedChinese, .permissionsPreviewBadge): "预览样例"
        case (.simplifiedChinese, .approvalPolicy): "审批策略"
        case (.simplifiedChinese, .permissionsAuthorityBoundary): "权限与审批边界"
        case (.simplifiedChinese, .permissionsAuthorityBoundaryBody):
            "云端传输、外部写入和强制终止都需要显式、一次性的任务绑定审批。"
            + "此预览绝不授予权限或执行审批。"
        case (.english, .permissionsTitle): "Permissions & Approvals"
        case (.english, .permissionsSyntheticOnly): "Six synthetic permission-scope examples for reviewing how the finished product presents permission scope and approval policy."
        case (.english, .permissionsPreviewBadge): "PREVIEW EXAMPLE"
        case (.english, .approvalPolicy): "Approval policy"
        case (.english, .permissionsAuthorityBoundary): "Permission and approval boundary"
        case (.english, .permissionsAuthorityBoundaryBody):
            "Cloud transmission, external writes, and force termination require explicit, "
            + "one-shot, task-bound approval. This preview never grants a permission or "
            + "performs an approval."
        }
    }

    func agentKindTitle(_ kind: AgentAdapterKind) -> String {
        switch (language, kind) {
        case (.simplifiedChinese, .herdrTerminal): "Herdr 终端 Agent"
        case (.simplifiedChinese, .codexCompatible): "Codex 兼容适配器"
        case (.simplifiedChinese, .claudeCompatible): "Claude 兼容适配器"
        case (.simplifiedChinese, .holaOSReference): "holaOS 工具参考"
        case (.english, .herdrTerminal): "Herdr terminal agent"
        case (.english, .codexCompatible): "Codex-compatible adapter"
        case (.english, .claudeCompatible): "Claude-compatible adapter"
        case (.english, .holaOSReference): "holaOS tool reference"
        }
    }

    func agentKindDetail(_ kind: AgentAdapterKind) -> String {
        switch (language, kind) {
        case (.simplifiedChinese, .herdrTerminal): "权威执行运行时：拥有进程、pane、语义状态、等待、取消与恢复。"
        case (.simplifiedChinese, .codexCompatible): "把 vendor-neutral 契约翻译到 Codex，不引入竞争状态机。"
        case (.simplifiedChinese, .claudeCompatible): "把 vendor-neutral 契约翻译到 Claude，不引入竞争状态机。"
        case (.simplifiedChinese, .holaOSReference): "仅外部安装参考：工作流/工具能力，禁止打包其前端。"
        case (.english, .herdrTerminal): "The authoritative execution runtime: owns processes, panes, semantic state, wait, cancel, and resume."
        case (.english, .codexCompatible): "Translates the vendor-neutral contract to Codex without a competing state machine."
        case (.english, .claudeCompatible): "Translates the vendor-neutral contract to Claude without a competing state machine."
        case (.english, .holaOSReference): "External-install reference only: workflow/tool capabilities; its frontend is never bundled."
        }
    }

    func permissionScopeTitle(_ scope: PermissionScope) -> String {
        switch (language, scope) {
        case (.simplifiedChinese, .read): "读取"
        case (.simplifiedChinese, .write): "写入"
        case (.simplifiedChinese, .send): "发送"
        case (.simplifiedChinese, .delete): "删除"
        case (.simplifiedChinese, .execute): "执行"
        case (.simplifiedChinese, .credential): "凭据"
        case (.english, .read): "Read"
        case (.english, .write): "Write"
        case (.english, .send): "Send"
        case (.english, .delete): "Delete"
        case (.english, .execute): "Execute"
        case (.english, .credential): "Credential"
        }
    }

    func permissionScopeDetail(_ scope: PermissionScope) -> String {
        switch (language, scope) {
        case (.simplifiedChinese, .read): "读取文件、笔记或检索结果，不改变外部状态。"
        case (.simplifiedChinese, .write): "写入或修改外部内容，需预览与批准。"
        case (.simplifiedChinese, .send): "向外发送消息或数据，需预览与批准。"
        case (.simplifiedChinese, .delete): "删除外部内容，需预览与批准且不可静默恢复。"
        case (.simplifiedChinese, .execute): "运行命令或进程，需作用域批准。"
        case (.simplifiedChinese, .credential): "访问凭据，仅存 Keychain，绝不进入日志或参数。"
        case (.english, .read): "Read files, notes, or retrieval results without changing external state."
        case (.english, .write): "Write or modify external content, requiring preview and approval."
        case (.english, .send): "Send messages or data outward, requiring preview and approval."
        case (.english, .delete): "Delete external content, requiring preview and approval with no silent restore."
        case (.english, .execute): "Run commands or processes, requiring scoped approval."
        case (.english, .credential): "Access credentials, held only in Keychain and never in logs or arguments."
        }
    }
}
