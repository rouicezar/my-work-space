import LifecycleContract

enum HistoryCopyKey {
    case historyTitle, historySyntheticOnly, previewBadge, whyThisState
    case lastVerified, agentsAndArtifacts, executionSummary
    case timelineGoal, timelineGoalValue, timelineWork, timelineStop
    case recoveryDecision, truthBoundary, truthBoundaryBody, recoveryPreviewResult
}

extension ProductCopy {
    subscript(key: HistoryCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .historyTitle): "任务历史"
        case (.simplifiedChinese, .historySyntheticOnly): "7 个合成样例，用于检查最终产品如何呈现状态与恢复。"
        case (.simplifiedChinese, .previewBadge): "预览样例"
        case (.simplifiedChinese, .whyThisState): "为什么是这个状态"
        case (.simplifiedChinese, .lastVerified): "最近可信状态"
        case (.simplifiedChinese, .agentsAndArtifacts): "Agent 与产物"
        case (.simplifiedChinese, .executionSummary): "执行摘要"
        case (.simplifiedChinese, .timelineGoal): "目标已记录"
        case (.simplifiedChinese, .timelineGoalValue): "形成一份可审核、带证据的项目简报。"
        case (.simplifiedChinese, .timelineWork): "工作进展"
        case (.simplifiedChinese, .timelineStop): "停止点"
        case (.simplifiedChinese, .recoveryDecision): "恢复决策"
        case (.simplifiedChinese, .truthBoundary): "真实性与审计边界"
        case (.simplifiedChinese, .truthBoundaryBody): "这里没有读取真实历史，也没有连接原生执行会话。正式产品会先获取新快照与修订号，再判断能否续跑；强制终止始终是单独的明确批准。"
        case (.simplifiedChinese, .recoveryPreviewResult): "已展示恢复后的界面位置；没有续跑、重试、取消、终止或持久化任何任务。"
        case (.english, .historyTitle): "Task history"
        case (.english, .historySyntheticOnly): "Seven synthetic examples for reviewing how the finished product presents state and recovery."
        case (.english, .previewBadge): "PREVIEW EXAMPLE"
        case (.english, .whyThisState): "Why this state"
        case (.english, .lastVerified): "Last trusted state"
        case (.english, .agentsAndArtifacts): "Agents and artifacts"
        case (.english, .executionSummary): "Execution summary"
        case (.english, .timelineGoal): "Goal recorded"
        case (.english, .timelineGoalValue): "Create a reviewable project brief with evidence."
        case (.english, .timelineWork): "Work progress"
        case (.english, .timelineStop): "Stopping point"
        case (.english, .recoveryDecision): "Recovery decision"
        case (.english, .truthBoundary): "Truth and audit boundary"
        case (.english, .truthBoundaryBody): "No real history is read and no native execution session is connected here. The finished product fetches a fresh snapshot and revision before deciding whether resume is valid. Force termination always requires a separate explicit approval."
        case (.english, .recoveryPreviewResult): "The post-recovery interface position is now visible. No task was resumed, retried, cancelled, terminated, or persisted."
        }
    }

    func stateTitle(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .interrupted): "已中断"
        case (.simplifiedChinese, .blocked): "已阻塞"
        case (.simplifiedChinese, .failed): "已失败"
        case (.simplifiedChinese, .partial): "部分完成"
        case (.simplifiedChinese, .cancelled): "已取消"
        case (.simplifiedChinese, .completed): "已完成"
        case (.simplifiedChinese, .unknown): "状态未知"
        case (.english, .interrupted): "Interrupted"
        case (.english, .blocked): "Blocked"
        case (.english, .failed): "Failed"
        case (.english, .partial): "Partial"
        case (.english, .cancelled): "Cancelled"
        case (.english, .completed): "Completed"
        case (.english, .unknown): "Unknown"
        }
    }

    func taskTitle(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .interrupted): "恢复研究简报"
        case (.simplifiedChinese, .blocked): "发送结果前等待批准"
        case (.simplifiedChinese, .failed): "分析附件失败"
        case (.simplifiedChinese, .partial): "市场扫描部分完成"
        case (.simplifiedChinese, .cancelled): "已取消竞品整理"
        case (.simplifiedChinese, .completed): "项目摘要已交付"
        case (.simplifiedChinese, .unknown): "执行状态需要对账"
        case (.english, .interrupted): "Resume the research brief"
        case (.english, .blocked): "Approval needed before delivery"
        case (.english, .failed): "Attachment analysis failed"
        case (.english, .partial): "Market scan partially complete"
        case (.english, .cancelled): "Competitor review cancelled"
        case (.english, .completed): "Project summary delivered"
        case (.english, .unknown): "Execution state needs reconciliation"
        }
    }

    func stateReason(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .interrupted): "应用退出时会话仍有可验证检查点，但必须先与最新原生会话修订号对账。"
        case (.simplifiedChinese, .blocked): "任务本身没有失败；一个外部写入需要用户查看范围并明确批准。"
        case (.simplifiedChinese, .failed): "附件解析步骤返回不可恢复错误，后续 Agent 未被启动。"
        case (.simplifiedChinese, .partial): "两项产物已验证，一项来源仍缺失，因此不能标记为完成。"
        case (.simplifiedChinese, .cancelled): "用户主动取消；保留既有审计记录，但不提供静默续跑。"
        case (.simplifiedChinese, .completed): "计划步骤、产物和验证均已结束，没有未解决项。"
        case (.simplifiedChinese, .unknown): "本地投影与运行时修订号不一致；在重新对账前不能声称成功或可恢复。"
        case (.english, .interrupted): "The app closed while a verifiable checkpoint existed, but it must be reconciled against the latest native session revision first."
        case (.english, .blocked): "The task did not fail. An external write is waiting for the user to inspect its scope and explicitly approve it."
        case (.english, .failed): "Attachment parsing returned a non-recoverable error, so downstream Agents were not started."
        case (.english, .partial): "Two artifacts are validated and one source is still missing, so the task cannot be marked complete."
        case (.english, .cancelled): "The user cancelled intentionally. Existing audit evidence remains, but no silent resume is offered."
        case (.english, .completed): "All plan steps, artifacts, and validations finished with no unresolved items."
        case (.english, .unknown): "The local projection and runtime revision disagree. Success or recoverability cannot be claimed before reconciliation."
        }
    }

    func lastVerified(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .interrupted): "检查点 4 · 等待对账"
        case (.simplifiedChinese, .blocked): "批准前暂停"
        case (.simplifiedChinese, .failed): "附件读取失败"
        case (.simplifiedChinese, .partial): "2/3 产物通过"
        case (.simplifiedChinese, .cancelled): "取消已确认"
        case (.simplifiedChinese, .completed): "全部验证通过"
        case (.simplifiedChinese, .unknown): "没有可信新快照"
        case (.english, .interrupted): "Checkpoint 4 · reconciliation pending"
        case (.english, .blocked): "Paused before approval"
        case (.english, .failed): "Attachment read failed"
        case (.english, .partial): "2 of 3 artifacts passed"
        case (.english, .cancelled): "Cancellation confirmed"
        case (.english, .completed): "All validation passed"
        case (.english, .unknown): "No trusted fresh snapshot"
        }
    }

    func agentSummary(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .completed): "3 个完成 · 2 个产物"
        case (.simplifiedChinese, .partial): "2 个完成 · 1 个未解决"
        case (.simplifiedChinese, .cancelled): "1 个已停止 · 无新产物"
        case (.simplifiedChinese, .unknown): "不可确认"
        case (.simplifiedChinese, _): "1 个已暂停 · 1 个草稿"
        case (.english, .completed): "3 complete · 2 artifacts"
        case (.english, .partial): "2 complete · 1 unresolved"
        case (.english, .cancelled): "1 stopped · no new artifact"
        case (.english, .unknown): "Cannot be confirmed"
        case (.english, _): "1 paused · 1 draft"
        }
    }

    func timelineWork(_ state: HistoryPreviewTaskState) -> String { stateReason(state) }

    func timelineStop(_ state: HistoryPreviewTaskState) -> String {
        switch language {
        case .simplifiedChinese: state == .completed ? "结果与审计记录已交付。" : "最终结果尚未成立；请查看下面的恢复决策。"
        case .english: state == .completed ? "Result and audit record delivered." : "No final result is established. Review the recovery decision below."
        }
    }

    func canPreviewRecovery(_ state: HistoryPreviewTaskState) -> Bool {
        [.interrupted, .blocked, .failed, .partial, .unknown].contains(state)
    }

    func recoveryEligibility(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .completed): "无需恢复"
        case (.simplifiedChinese, .cancelled): "取消后不自动续跑"
        case (.simplifiedChinese, .unknown): "必须先对账"
        case (.simplifiedChinese, _): "仅展示决策，不执行"
        case (.english, .completed): "No recovery needed"
        case (.english, .cancelled): "No automatic resume after cancellation"
        case (.english, .unknown): "Reconciliation required first"
        case (.english, _): "Decision preview only"
        }
    }

    func recoveryExplanation(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .interrupted): "先获取新快照并核对修订号；匹配后才允许从已验证检查点续跑，也可以明确选择重新开始。"
        case (.simplifiedChinese, .blocked): "保留当前工作，向用户展示动作、目的地与影响；批准与拒绝都必须进入审计。"
        case (.simplifiedChinese, .failed): "展示失败证据与影响范围；用户可以选择从失败步骤重试或新建任务。"
        case (.simplifiedChinese, .partial): "保留已验证产物，只为未解决项提出后续任务，不能覆盖为‘已完成’。"
        case (.simplifiedChinese, .cancelled): "取消是终态。需要继续时应明确创建新任务，而不是恢复旧会话。"
        case (.simplifiedChinese, .completed): "结果已完成且验证通过，因此不展示恢复动作。"
        case (.simplifiedChinese, .unknown): "禁用续跑和终态判断，先从原生执行层获取可信新快照并完成修订号对账。"
        case (.english, .interrupted): "Fetch a fresh snapshot and compare revisions first. Resume from the verified checkpoint only after they match, or explicitly start over."
        case (.english, .blocked): "Keep current work and show the action, destination, and impact. Both approval and decline must be audited."
        case (.english, .failed): "Show the failure evidence and affected scope. The user may retry the failed step or create a fresh task."
        case (.english, .partial): "Keep validated artifacts and propose follow-up only for unresolved items. Never overwrite this state as complete."
        case (.english, .cancelled): "Cancellation is terminal. Continuing requires an explicit new task, not resuming the old session."
        case (.english, .completed): "The result is complete and validated, so no recovery action is offered."
        case (.english, .unknown): "Disable resume and terminal claims. Fetch a trusted fresh snapshot from the native execution layer and reconcile its revision first."
        }
    }

    func recoveryAction(_ state: HistoryPreviewTaskState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .interrupted): "预览对账后续跑"
        case (.simplifiedChinese, .blocked): "预览批准决策"
        case (.simplifiedChinese, .failed): "预览重试选择"
        case (.simplifiedChinese, .partial): "预览未解决项后续"
        case (.simplifiedChinese, .unknown): "预览对账流程"
        case (.simplifiedChinese, _): "查看"
        case (.english, .interrupted): "Preview reconciled resume"
        case (.english, .blocked): "Preview approval decision"
        case (.english, .failed): "Preview retry choices"
        case (.english, .partial): "Preview unresolved follow-up"
        case (.english, .unknown): "Preview reconciliation"
        case (.english, _): "View"
        }
    }
}
