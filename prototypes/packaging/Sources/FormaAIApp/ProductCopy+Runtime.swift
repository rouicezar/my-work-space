import LifecycleContract

extension ProductCopy {

    var runtimeCheckingRoute: String {
        language == .simplifiedChinese ? "正在检查最安全的可用路线…" : "Checking the safest available route…"
    }

    var taskPrivacySubtitle: String {
        language == .simplifiedChinese ? "默认保护隐私 · 使用云端前始终先询问" : "Private by default · cloud use always asks first"
    }

    var taskNewTaskButton: String { language == .simplifiedChinese ? "新建任务" : "New task" }

    var taskCloudBoundary: String {
        language == .simplifiedChinese
            ? "此任务超出已验证的本地边界。尚未有任何内容离开这台 Mac。"
            : "This task is outside the verified local boundary. Nothing has left this Mac."
    }

    var taskCloudCredentialHint: String {
        language == .simplifiedChinese
            ? "只有在设置中配置用户提供的凭据后，才会启用云端批准与执行。"
            : "Cloud approval and execution will be enabled only after a user-provided credential is configured in Settings."
    }

    var taskDeniedBody: String {
        language == .simplifiedChinese ? "你已拒绝此提议，待发送内容已被移除。" : "You declined this proposal. Its pending payload was removed."
    }

    var taskApprovalRequired: String { language == .simplifiedChinese ? "需要你批准" : "Your approval is required" }
    var taskCompletedLocal: String { language == .simplifiedChinese ? "已在本地完成" : "Completed locally" }
    var taskCloudExecuting: String { language == .simplifiedChinese ? "正在执行已批准的云端任务" : "Running approved cloud task" }
    var taskCloudCompleted: String { language == .simplifiedChinese ? "已通过批准的云端使用完成" : "Completed with approved cloud use" }
    var taskDeniedTitle: String { language == .simplifiedChinese ? "云端请求未发送" : "Cloud request not sent" }
    var taskUnavailableTitle: String { language == .simplifiedChinese ? "此任务无法安全运行" : "This task cannot run safely" }
    var taskFailedTitle: String { language == .simplifiedChinese ? "任务已安全停止" : "Task stopped safely" }

    var wouldSend: String { language == .simplifiedChinese ? "将发送" : "Would send" }
    var dataLabel: String { language == .simplifiedChinese ? "数据" : "Data" }
    var locationLabel: String { language == .simplifiedChinese ? "位置" : "Location" }
    var maxCostLabel: String { language == .simplifiedChinese ? "最高成本" : "Maximum cost" }
    var approveAndRun: String { language == .simplifiedChinese ? "批准并运行" : "Approve and run" }
    var dontSend: String { language == .simplifiedChinese ? "不要发送" : "Don't send" }
    var proposalOnly: String { language == .simplifiedChinese ? "仅为提议 · 未发起网络请求" : "Proposal only · no network request" }
    var openRecoverySettings: String { language == .simplifiedChinese ? "打开恢复设置" : "Open recovery settings" }

    func actualCost(_ value: Double) -> String {
        language == .simplifiedChinese
            ? "实际成本 · \(String(format: "$%.6f", value))"
            : "Actual cost · \(String(format: "$%.6f", value))"
    }

    func localModelRoute(_ model: String) -> String {
        language == .simplifiedChinese ? "本地模型 · \(model)" : "Local model · \(model)"
    }

    func approvedCloudRoute(_ model: String) -> String {
        language == .simplifiedChinese ? "已批准云端 · \(model)" : "Approved cloud · \(model)"
    }

    func auditCorrelation(_ id: String) -> String {
        language == .simplifiedChinese ? "审计 · \(id)" : "Audit · \(id)"
    }

    var parallelAgents: String { language == .simplifiedChinese ? "并行 Agent" : "Parallel agents" }
    func paneLabel(_ id: String) -> String { language == .simplifiedChinese ? "面板 \(id)" : "Pane \(id)" }
    func workspaceLine(workspace: String, tab: String, terminal: String) -> String {
        language == .simplifiedChinese
            ? "工作区 \(workspace) · 标签页 \(tab) · 终端 \(terminal)"
            : "Workspace \(workspace) · Tab \(tab) · Terminal \(terminal)"
    }

    func agentStatusLabel(_ status: String) -> String {
        switch (language, status) {
        case (.simplifiedChinese, "working"): "工作中"
        case (.simplifiedChinese, "blocked"): "受阻"
        case (.simplifiedChinese, "idle"): "空闲"
        case (.simplifiedChinese, "done"): "完成"
        case (.simplifiedChinese, _): status
        case (.english, _): status.capitalized
        }
    }

    var agentActivityChecking: String { language == .simplifiedChinese ? "正在检查 Herdr…" : "Checking Herdr…" }
    var agentActivityLive: String { language == .simplifiedChinese ? "Herdr 实时" : "Live from Herdr" }
    var agentActivityHerdrStopped: String { language == .simplifiedChinese ? "Herdr 未运行" : "Herdr not running" }
    func agentActivityDisconnected(_ reason: String) -> String {
        language == .simplifiedChinese ? "已断开：\(reason)" : "Disconnected: \(reason)"
    }
    var agentActivityDisconnectedGeneric: String { language == .simplifiedChinese ? "已断开" : "Disconnected" }
    var agentActivityStartRuntime: String {
        language == .simplifiedChinese ? "启动本地运行时以查看实时 Agent 活动。" : "Start the local runtime to see live agent activity."
    }
    var agentActivityNone: String { language == .simplifiedChinese ? "当前没有活跃的 Agent。" : "No agents are active right now." }
    var agentActivityUnavailable: String { language == .simplifiedChinese ? "Agent 活动不可用。" : "Agent activity is unavailable." }

    var optionalCloudAI: String { language == .simplifiedChinese ? "可选云端 AI" : "Optional cloud AI" }
    func cloudModelApprovalNote(_ model: String) -> String {
        language == .simplifiedChinese
            ? "\(model) · 每次请求仍须单独预览并批准"
            : "\(model) · every request still requires a separate preview and approval"
    }
    func cloudPayloadSummary(bytes: Int, model: String) -> String {
        language == .simplifiedChinese
            ? "\(bytes) 字节 → \(model)"
            : "\(bytes) bytes to \(model)"
    }
    var cloudExecutingDetail: String {
        language == .simplifiedChinese
            ? "仅发送已批准的内容并验证响应…"
            : "Sending only the approved payload and validating the response…"
    }

    var cloudOffTitle: String { language == .simplifiedChinese ? "云端 AI 已关闭" : "Cloud AI is off" }
    var cloudOffDetail: String {
        language == .simplifiedChinese
            ? "本地 AI 仍是默认选项。添加 DeepSeek API Key 后可启用按任务批准的云端提议。"
            : "Local AI remains the default. Add your own DeepSeek API key to allow task-bound approval proposals."
    }
    var deepSeekKey: String { language == .simplifiedChinese ? "DeepSeek API Key" : "DeepSeek API key" }
    var saveEnableCloud: String { language == .simplifiedChinese ? "保存到钥匙串并启用" : "Save in Keychain and enable" }
    var cloudAvailable: String { language == .simplifiedChinese ? "云端 AI 可用（需批准）" : "Cloud AI available with approval" }
    var cloudStored: String {
        language == .simplifiedChinese
            ? "DeepSeek 凭据已保存在本机钥匙串，界面不会显示其值。"
            : "DeepSeek credential is stored in this Mac's Keychain. Its value is never displayed."
    }
    var replaceCloudKey: String { language == .simplifiedChinese ? "替换 DeepSeek API Key" : "Replace DeepSeek API key" }
    var replaceCredential: String { language == .simplifiedChinese ? "替换凭据" : "Replace credential" }
    var disableCloud: String { language == .simplifiedChinese ? "禁用云端并移除密钥" : "Disable cloud and remove key" }
    var cloudNeedsAttention: String { language == .simplifiedChinese ? "云端设置需要处理" : "Cloud settings need attention" }
    var checkAgain: String { language == .simplifiedChinese ? "重新检查" : "Check again" }
    var checkingCloud: String { language == .simplifiedChinese ? "正在检查私有云端设置…" : "Checking private cloud settings…" }
    var updatingCloud: String { language == .simplifiedChinese ? "正在更新钥匙串与私有路由偏好…" : "Updating Keychain and private routing preference…" }

    var runtimeReady: String { language == .simplifiedChinese ? "本地 AI 就绪" : "Local AI ready" }
    var runtimeChecking: String { language == .simplifiedChinese ? "正在检查本地 AI" : "Checking local AI" }
    var runtimeStopped: String { language == .simplifiedChinese ? "本地 AI 已停止" : "Local AI stopped" }
    var runtimeRecovery: String { language == .simplifiedChinese ? "需要恢复" : "Recovery needed" }
    var runtimeUnavailable: String { language == .simplifiedChinese ? "状态不可用" : "Status unavailable" }

    func modelRouteTitle(_ choice: ModelRouteChoice) -> String {
        switch (language, choice) {
        case (.simplifiedChinese, .automaticLocalFirst): "自动 · 本地优先"
        case (.simplifiedChinese, .localOnly): "仅本地"
        case (.simplifiedChinese, .cloudWithApproval): "云端 · 每次询问"
        case (.english, .automaticLocalFirst): "Automatic · local first"
        case (.english, .localOnly): "Local only"
        case (.english, .cloudWithApproval): "Cloud · ask every time"
        }
    }
}
