import LifecycleContract

extension ProductCopy {
    var historyLoading: String { language == .simplifiedChinese ? "正在加载已对账任务历史…" : "Loading reconciled task history…" }
    var historyUnavailable: String { language == .simplifiedChinese ? "任务历史不可用" : "Task history unavailable" }
    var historyStartRuntimeHint: String {
        language == .simplifiedChinese
            ? "请先启动本地运行时并确保 Herdr 正在运行，再执行恢复操作。"
            : "Start the local runtime and ensure Herdr is running before recovery actions."
    }
    var tryAgain: String { language == .simplifiedChinese ? "重试" : "Try again" }
    var refreshReconcile: String { language == .simplifiedChinese ? "刷新对账" : "Refresh reconcile" }
    func auditPath(_ path: String) -> String { language == .simplifiedChinese ? "审计 · \(path)" : "Audit: \(path)" }
    var historyActing: String { language == .simplifiedChinese ? "正在应用 Herdr 恢复操作…" : "Applying Herdr recovery action…" }
    var historyFailedSafely: String { language == .simplifiedChinese ? "恢复已安全失败" : "Recovery failed safely" }
    func runtimeAuthority(_ value: String) -> String {
        language == .simplifiedChinese ? "运行时权威 · \(value)" : "Runtime authority: \(value)"
    }
    func freshness(_ value: String) -> String {
        language == .simplifiedChinese ? "新鲜度 · \(value)" : "Freshness: \(value)"
    }
    var persistedTasks: String { language == .simplifiedChinese ? "持久化任务" : "Persisted tasks" }
    var noPersistedTasks: String {
        language == .simplifiedChinese ? "尚无持久化任务元数据。" : "No persisted task metadata yet."
    }
    var selectTaskHint: String {
        language == .simplifiedChinese ? "选择一个任务以查看已对账的运行时真相。" : "Select a task to inspect reconciled runtime truth."
    }
    var recoveryHerdrAuthority: String { language == .simplifiedChinese ? "恢复（Herdr 权威）" : "Recovery (Herdr authority)" }
    var reclaimSession: String { language == .simplifiedChinese ? "收回会话" : "Reclaim session" }
    var cancelGracefully: String { language == .simplifiedChinese ? "优雅取消" : "Cancel gracefully" }
    var freshRunPanePlaceholder: String { language == .simplifiedChinese ? "全新运行面板 ID" : "Fresh-run pane id" }
    var startFreshRun: String { language == .simplifiedChinese ? "全新开始" : "Start fresh run" }
    var recoveryRevisionHint: String {
        language == .simplifiedChinese
            ? "恢复路径需要最新的 Herdr 快照与匹配的修订号。界面不会伪造完成或可恢复状态。"
            : "Recovery routes require a fresh Herdr snapshot and matching revision. The UI never manufactures completion or resumability."
    }
    var reconciliationRequired: String {
        language == .simplifiedChinese ? "恢复前必须先完成对账" : "Reconciliation required before recovery"
    }
    func detailLabel(_ key: HistoryDetailKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .outcome): "结果"
        case (.simplifiedChinese, .runtimeState): "运行时状态"
        case (.simplifiedChinese, .revision): "修订号"
        case (.simplifiedChinese, .pane): "面板"
        case (.english, .outcome): "Outcome"
        case (.english, .runtimeState): "Runtime state"
        case (.english, .revision): "Revision"
        case (.english, .pane): "Pane"
        }
    }

    var memoryReviewTitle: String { language == .simplifiedChinese ? "记忆审核" : "Memory review" }
    var memoryLoading: String { language == .simplifiedChinese ? "正在加载受治理记忆快照…" : "Loading governed memory snapshot…" }
    var memoryUnavailable: String { language == .simplifiedChinese ? "记忆服务不可用" : "Memory service unavailable" }
    var memoryStartRuntimeHint: String {
        language == .simplifiedChinese
            ? "请先启动本地运行时，并确保受治理记忆服务在 loopback 上监听。"
            : "Start the local runtime and ensure the governed-memory service is listening on loopback."
    }
    var refreshSnapshot: String { language == .simplifiedChinese ? "刷新快照" : "Refresh snapshot" }
    var memoryActing: String { language == .simplifiedChinese ? "正在记录审核决策…" : "Recording review decision…" }
    var memoryFailedSafely: String { language == .simplifiedChinese ? "记忆审核已安全失败" : "Memory review failed safely" }
    func confirmedAuthority(_ value: String) -> String {
        language == .simplifiedChinese ? "确认权威 · \(value)" : "Confirmed authority: \(value)"
    }
    func loopbackPort(_ port: Int) -> String { "Loopback :\(port)" }
    var pendingCandidates: String { language == .simplifiedChinese ? "待审候选" : "Pending candidates" }
    var confirmedRecords: String { language == .simplifiedChinese ? "已确认记录" : "Confirmed records" }
    var noMemoryRecords: String {
        language == .simplifiedChinese ? "没有待审候选或已确认记录。" : "No pending candidates or confirmed records."
    }
    var selectMemoryRecord: String {
        language == .simplifiedChinese ? "选择一个候选或已确认记录。" : "Select a candidate or confirmed record."
    }
    var confirmToSemantica: String { language == .simplifiedChinese ? "确认写入 Semantica" : "Confirm to Semantica" }
    var reject: String { language == .simplifiedChinese ? "拒绝" : "Reject" }
    func confirmedVersion(_ version: Int) -> String {
        language == .simplifiedChinese ? "已确认 v\(version)" : "confirmed v\(version)"
    }

    func composerSafetyDescription(_ choice: ModelRouteChoice) -> String {
        switch (language, choice) {
        case (.simplifiedChinese, .automaticLocalFirst):
            "默认本地处理。任何云端提议在你批准确切请求前都不会发送数据。"
        case (.simplifiedChinese, .localOnly):
            "仅本地偏好会保存到本任务，但提交会等待 Supervisor 路由契约接受后再执行。"
        case (.simplifiedChinese, .cloudWithApproval):
            "云端偏好不等于授权发送。仍需要凭据、确切载荷预览和单独批准。"
        case (.english, .automaticLocalFirst):
            "Local by default. A cloud proposal never sends data until you approve the exact request."
        case (.english, .localOnly):
            "Local-only preference is saved for this task, but submission waits until the Supervisor routing contract accepts it."
        case (.english, .cloudWithApproval):
            "Cloud preference never authorizes sending. A credential, exact payload preview, and separate approval are still required."
        }
    }

    var firstRunRetry: String { language == .simplifiedChinese ? "重试" : "Retry" }
    var productionLocalRuntimeSubtitle: String {
        language == .simplifiedChinese
            ? "启动、停止并验证本机本地 AI 服务。只有验证通过后才应提交任务。"
            : "Start, stop, and verify local AI on this Mac. Submit tasks only after verification succeeds."
    }
    var startLocalRuntime: String { language == .simplifiedChinese ? "启动本地 AI" : "Start local AI" }
    var stopLocalRuntime: String { language == .simplifiedChinese ? "停止本地 AI" : "Stop local AI" }
    var verifyLocalRuntime: String { language == .simplifiedChinese ? "运行验证任务" : "Run verification" }
    var refreshStatus: String { language == .simplifiedChinese ? "刷新状态" : "Refresh" }
    var supervisorUnavailable: String {
        language == .simplifiedChinese ? "Supervisor 不可用，请重新安装或修复 Forma AI。" : "Supervisor is unavailable. Reinstall or repair Forma AI."
    }
    func runtimeCardTitle(_ state: RuntimeViewState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .loading): "正在检查本地运行时…"
        case (.simplifiedChinese, .stopped): "本地 AI 已停止"
        case (.simplifiedChinese, .starting): "正在启动本地 AI…"
        case (.simplifiedChinese, .running): "本地 AI 正在运行"
        case (.simplifiedChinese, .sampling): "正在运行验证任务…"
        case (.simplifiedChinese, .sample): "验证成功"
        case (.simplifiedChinese, .degraded): "本地 AI 需要关注"
        case (.simplifiedChinese, .failed): "本地 AI 不可用"
        case (.english, .loading): "Checking local runtime…"
        case (.english, .stopped): "Local AI is stopped"
        case (.english, .starting): "Starting local AI…"
        case (.english, .running): "Local AI is running"
        case (.english, .sampling): "Running verification…"
        case (.english, .sample): "Verification succeeded"
        case (.english, .degraded): "Local AI needs attention"
        case (.english, .failed): "Local AI is unavailable"
        }
    }
    var productionModelsSubtitle: String {
        language == .simplifiedChinese
            ? "Forma AI 会在这台 Mac 的应用支持目录中下载并验证推荐模型。"
            : "Forma AI downloads and verifies the recommended model inside this Mac's Application Support directory."
    }
    var prepareLocalModel: String { language == .simplifiedChinese ? "准备/修复本地模型" : "Prepare or repair local model" }
    var productionModelsRouteNote: String {
        language == .simplifiedChinese
            ? "当前版本仅「自动·本地优先」可直接提交任务。其他路线会在后续版本开放。"
            : "Only Automatic · local first can submit tasks in this version. Other routes will open later."
    }
    func downloadProgress(transferred: Int64, total: Int64) -> String {
        let pct = total > 0 ? Int((Double(transferred) / Double(total)) * 100) : 0
        return language == .simplifiedChinese
            ? "已下载 \(pct)% · \(transferred)/\(total) 字节"
            : "Downloaded \(pct)% · \(transferred)/\(total) bytes"
    }
    var productionDiagnosticsSubtitle: String {
        language == .simplifiedChinese
            ? "查看系统检查结果，并在需要时从真实任务历史中恢复。"
            : "Review system checks and recover from real task history when needed."
    }
    var systemChecks: String { language == .simplifiedChinese ? "系统检查" : "System checks" }
    var runningChecks: String { language == .simplifiedChinese ? "正在运行检查…" : "Running checks…" }
    var preflightStatus: String { language == .simplifiedChinese ? "硬件/环境预检" : "Hardware/environment preflight" }
    var installationStatus: String { language == .simplifiedChinese ? "组件安装状态" : "Component installation" }
}


enum HistoryDetailKey {
    case outcome, runtimeState, revision, pane
}
