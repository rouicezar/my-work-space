import LifecycleContract

enum DailyCopyKey {
    case previewNotice
    case newTask
    case history
    case settings
    case recentTasks
    case noRealHistory
    case sampleTask
    case sampleBadge
    case languageControl
    case simplifiedChinese
    case english
    case greeting
    case promptTitle
    case promptPlaceholder
    case promptHint
    case context
    case contextExplanation
    case previewContext
    case route
    case localRoute
    case localRouteDetail
    case cloudRoute
    case cloudRouteDetail
    case privacyTitle
    case privacyDetail
    case previewPlan
    case previewPlanExplanation
    case starterTitle
    case starterResearch
    case starterWriting
    case starterPlanning
    case supervision
    case collapseSupervision
    case expandSupervision
    case noActiveTask
    case supervisionExplanation
    case agentStatus
    case waitingForTask
    case evidenceStatus
    case nothingProduced
    case contextPreviewTitle
    case contextPreviewBody
    case dismiss
    case startTask
    case startTaskExplanation
    case contextUnavailable
    case routeBindingRequired
}

struct ProductCopy {
    let language: ProductLanguage

    subscript(key: DailyCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .previewNotice): "产品预览 · 合成数据 · 不会执行任务"
        case (.simplifiedChinese, .newTask): "新任务"
        case (.simplifiedChinese, .history): "历史"
        case (.simplifiedChinese, .settings): "设置"
        case (.simplifiedChinese, .recentTasks): "最近任务"
        case (.simplifiedChinese, .noRealHistory): "尚无真实任务。下面仅展示一个预览样例。"
        case (.simplifiedChinese, .sampleTask): "样例：整理项目研究材料"
        case (.simplifiedChinese, .sampleBadge): "预览"
        case (.simplifiedChinese, .languageControl): "语言"
        case (.simplifiedChinese, .simplifiedChinese): "简体中文"
        case (.simplifiedChinese, .english): "English"
        case (.simplifiedChinese, .greeting): "今天想完成什么？"
        case (.simplifiedChinese, .promptTitle): "描述你要的结果"
        case (.simplifiedChinese, .promptPlaceholder): "例如：梳理这批资料，找出关键结论，并生成一份可以审核的简报……"
        case (.simplifiedChinese, .promptHint): "先说结果，不必先决定模型、工具或 Agent。Forma AI 会提出路径供你审核。"
        case (.simplifiedChinese, .context): "上下文"
        case (.simplifiedChinese, .contextExplanation): "添加文件、文件夹或已有资料。预览不会读取任何内容。"
        case (.simplifiedChinese, .previewContext): "查看上下文入口"
        case (.simplifiedChinese, .route): "执行路径"
        case (.simplifiedChinese, .localRoute): "本地优先"
        case (.simplifiedChinese, .localRouteDetail): "默认留在这台 Mac 上，适合隐私内容和多数日常任务。"
        case (.simplifiedChinese, .cloudRoute): "必要时提议云端"
        case (.simplifiedChinese, .cloudRouteDetail): "只有本地能力不足时才提出，并在发送前展示范围、模型与成本。"
        case (.simplifiedChinese, .privacyTitle): "隐私边界清晰可见"
        case (.simplifiedChinese, .privacyDetail): "任何云端传输或外部写入都必须先经过你的明确批准。"
        case (.simplifiedChinese, .previewPlan): "预览任务计划"
        case (.simplifiedChinese, .previewPlanExplanation): "当前按钮仅展示最终交互位置；P4‑T12C 才连接确定性的输入到执行预览。"
        case (.simplifiedChinese, .starterTitle): "也可以从这些目标开始"
        case (.simplifiedChinese, .starterResearch): "研究并形成有证据的结论"
        case (.simplifiedChinese, .starterWriting): "把材料整理成可交付文稿"
        case (.simplifiedChinese, .starterPlanning): "拆解目标并监督并行工作"
        case (.simplifiedChinese, .supervision): "监督"
        case (.simplifiedChinese, .collapseSupervision): "收起监督栏"
        case (.simplifiedChinese, .expandSupervision): "展开监督栏"
        case (.simplifiedChinese, .noActiveTask): "没有正在执行的任务"
        case (.simplifiedChinese, .supervisionExplanation): "任务开始后，这里会显示计划、并行 Agent、批准、产物和验证状态。"
        case (.simplifiedChinese, .agentStatus): "Agent 状态"
        case (.simplifiedChinese, .waitingForTask): "等待任务"
        case (.simplifiedChinese, .evidenceStatus): "证据与产物"
        case (.simplifiedChinese, .nothingProduced): "尚未产生内容"
        case (.simplifiedChinese, .contextPreviewTitle): "上下文入口预览"
        case (.simplifiedChinese, .contextPreviewBody): "正式产品可选择文件、文件夹和已有任务材料。本预览不会打开选择器，也不会读取文件。"
        case (.simplifiedChinese, .dismiss): "知道了"
        case (.simplifiedChinese, .startTask): "开始任务"
        case (.simplifiedChinese, .startTaskExplanation): "Forma AI 会先检查最安全的可用路线，本地优先；需要云端时会先征求你的批准。"
        case (.simplifiedChinese, .contextUnavailable): "即将支持"
        case (.simplifiedChinese, .routeBindingRequired): "当前路线尚未绑定到可执行路由，请先在设置中完成运行时绑定。"

        case (.english, .previewNotice): "Product Preview · synthetic data · no runtime action"
        case (.english, .newTask): "New task"
        case (.english, .history): "History"
        case (.english, .settings): "Settings"
        case (.english, .recentTasks): "Recent tasks"
        case (.english, .noRealHistory): "No real tasks yet. The item below is a preview example only."
        case (.english, .sampleTask): "Example: organize project research"
        case (.english, .sampleBadge): "PREVIEW"
        case (.english, .languageControl): "Language"
        case (.english, .simplifiedChinese): "简体中文"
        case (.english, .english): "English"
        case (.english, .greeting): "What would you like to accomplish today?"
        case (.english, .promptTitle): "Describe the outcome you want"
        case (.english, .promptPlaceholder): "For example: review these materials, identify the key findings, and create a brief I can verify…"
        case (.english, .promptHint): "Start with the outcome. You do not need to choose a model, tool, or Agent first—Forma AI proposes a route for review."
        case (.english, .context): "Context"
        case (.english, .contextExplanation): "Add files, folders, or existing material. Preview reads nothing."
        case (.english, .previewContext): "Preview context options"
        case (.english, .route): "Execution route"
        case (.english, .localRoute): "Local first"
        case (.english, .localRouteDetail): "Stays on this Mac by default—best for private content and most everyday work."
        case (.english, .cloudRoute): "Propose cloud when needed"
        case (.english, .cloudRouteDetail): "Proposed only when local capability is insufficient, with scope, model, and cost shown before transmission."
        case (.english, .privacyTitle): "A visible privacy boundary"
        case (.english, .privacyDetail): "Every cloud transmission or external write requires your explicit approval first."
        case (.english, .previewPlan): "Preview task plan"
        case (.english, .previewPlanExplanation): "This control shows the final interaction position only. P4‑T12C connects the deterministic compose-to-execution preview."
        case (.english, .starterTitle): "Or start with an outcome"
        case (.english, .starterResearch): "Research and form evidence-backed conclusions"
        case (.english, .starterWriting): "Turn source material into a deliverable draft"
        case (.english, .starterPlanning): "Break down a goal and supervise parallel work"
        case (.english, .supervision): "Supervision"
        case (.english, .collapseSupervision): "Collapse supervision rail"
        case (.english, .expandSupervision): "Expand supervision rail"
        case (.english, .noActiveTask): "No task is running"
        case (.english, .supervisionExplanation): "After a task starts, its plan, parallel Agents, approvals, artifacts, and validation appear here."
        case (.english, .agentStatus): "Agent status"
        case (.english, .waitingForTask): "Waiting for a task"
        case (.english, .evidenceStatus): "Evidence and artifacts"
        case (.english, .nothingProduced): "Nothing produced yet"
        case (.english, .contextPreviewTitle): "Context options preview"
        case (.english, .contextPreviewBody): "The finished product can select files, folders, and material from existing tasks. This Preview opens no picker and reads no files."
        case (.english, .dismiss): "Got it"
        case (.english, .startTask): "Start task"
        case (.english, .startTaskExplanation): "Forma AI checks the safest available route first—local by default, with a separate approval step before any cloud use."
        case (.english, .contextUnavailable): "Coming soon"
        case (.english, .routeBindingRequired): "This route is not execution-bound yet. Finish runtime binding in Settings before submitting."
        }
    }
}

enum JourneyCopyKey {
    case stageCompose
    case stageRoute
    case stagePlan
    case stageParallel
    case stageApproval
    case stageValidation
    case stageResult
    case journeyPreview
    case syntheticGoal
    case routeHeadline
    case routeBody
    case routeLocalReason
    case routeCloudBoundary
    case planHeadline
    case planBody
    case planResearch
    case planAnalyze
    case planDraft
    case parallelHeadline
    case parallelBody
    case agentResearch
    case agentAnalysis
    case agentDraft
    case statusComplete
    case statusRunningPreview
    case statusQueuedPreview
    case approvalHeadline
    case approvalBody
    case approvalAction
    case approvalScope
    case approvalDestination
    case approvalDestinationValue
    case approvalEffectLabel
    case approvalEffect
    case approvalPreviewOnly
    case validationHeadline
    case validationBody
    case artifactNotes
    case artifactBrief
    case checkSources
    case checkStructure
    case checkPrivacy
    case valid
    case resultHeadline
    case resultBody
    case resultSummary
    case resultEvidence
    case resultUnresolved
    case none
    case nextPreview
    case showApprovedPreview
    case showValidationPreview
    case showResultPreview
    case backToEdit
    case previewStateNotice
}

extension ProductCopy {
    subscript(key: JourneyCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .stageCompose): "输入"
        case (.simplifiedChinese, .stageRoute): "路由审核"
        case (.simplifiedChinese, .stagePlan): "计划"
        case (.simplifiedChinese, .stageParallel): "并行执行"
        case (.simplifiedChinese, .stageApproval): "批准"
        case (.simplifiedChinese, .stageValidation): "验证"
        case (.simplifiedChinese, .stageResult): "结果"
        case (.simplifiedChinese, .journeyPreview): "任务流程预览"
        case (.simplifiedChinese, .syntheticGoal): "预览目标"
        case (.simplifiedChinese, .routeHeadline): "先确认 Forma AI 将如何处理这个任务"
        case (.simplifiedChinese, .routeBody): "本地路径被优先选中；任何能力不足或外部动作都会在继续前明确显示。"
        case (.simplifiedChinese, .routeLocalReason): "当前内容适合留在这台 Mac 上处理。"
        case (.simplifiedChinese, .routeCloudBoundary): "没有云端传输，也不会静默切换模型。"
        case (.simplifiedChinese, .planHeadline): "把目标拆成可监督的工作计划"
        case (.simplifiedChinese, .planBody): "每一步都有明确责任和可检查输出；这只是合成计划，不会创建 Agent。"
        case (.simplifiedChinese, .planResearch): "收集并标记相关材料"
        case (.simplifiedChinese, .planAnalyze): "比较证据并提炼关键发现"
        case (.simplifiedChinese, .planDraft): "形成可审核的结果与证据摘要"
        case (.simplifiedChinese, .parallelHeadline): "三个 Agent 并行协作，状态始终可见"
        case (.simplifiedChinese, .parallelBody): "这里展示未来真实执行时的责任、进度和交接形态；当前没有启动任何进程。"
        case (.simplifiedChinese, .agentResearch): "资料 Agent"
        case (.simplifiedChinese, .agentAnalysis): "分析 Agent"
        case (.simplifiedChinese, .agentDraft): "成稿 Agent"
        case (.simplifiedChinese, .statusComplete): "已完成预览"
        case (.simplifiedChinese, .statusRunningPreview): "正在运行的合成状态"
        case (.simplifiedChinese, .statusQueuedPreview): "等待上游输出"
        case (.simplifiedChinese, .approvalHeadline): "在外部动作发生前暂停并说明范围"
        case (.simplifiedChinese, .approvalBody): "这个批准卡展示用户最终会看到的信息，但不会执行批准或写入任何目的地。"
        case (.simplifiedChinese, .approvalAction): "建议动作"
        case (.simplifiedChinese, .approvalScope): "发送已验证的结果摘要"
        case (.simplifiedChinese, .approvalDestination): "目的地"
        case (.simplifiedChinese, .approvalDestinationValue): "合成项目工作区"
        case (.simplifiedChinese, .approvalEffectLabel): "影响"
        case (.simplifiedChinese, .approvalEffect): "一次性外部写入；不会建立长期授权"
        case (.simplifiedChinese, .approvalPreviewOnly): "下一步只展示‘已批准’后的预览状态。"
        case (.simplifiedChinese, .validationHeadline): "在给出结果前检查产物和证据"
        case (.simplifiedChinese, .validationBody): "验证状态与结果分开显示，避免把生成成功误报为任务完成。"
        case (.simplifiedChinese, .artifactNotes): "来源笔记"
        case (.simplifiedChinese, .artifactBrief): "可审核简报"
        case (.simplifiedChinese, .checkSources): "来源覆盖"
        case (.simplifiedChinese, .checkStructure): "结构完整"
        case (.simplifiedChinese, .checkPrivacy): "隐私边界"
        case (.simplifiedChinese, .valid): "通过"
        case (.simplifiedChinese, .resultHeadline): "结果、证据和未解决项一起交付"
        case (.simplifiedChinese, .resultBody): "这是合成结果页，用于验证最终阅读顺序，不代表真实模型或 Agent 已完成任务。"
        case (.simplifiedChinese, .resultSummary): "已形成一份结构化简报，包含关键发现、证据依据和下一步建议。"
        case (.simplifiedChinese, .resultEvidence): "2 个合成产物 · 3 项验证通过"
        case (.simplifiedChinese, .resultUnresolved): "未解决项"
        case (.simplifiedChinese, .none): "无"
        case (.simplifiedChinese, .nextPreview): "查看下一预览状态"
        case (.simplifiedChinese, .showApprovedPreview): "查看批准后状态"
        case (.simplifiedChinese, .showValidationPreview): "查看验证状态"
        case (.simplifiedChinese, .showResultPreview): "查看结果状态"
        case (.simplifiedChinese, .backToEdit): "返回编辑"
        case (.simplifiedChinese, .previewStateNotice): "所有状态均为确定性合成数据，不会执行任务、批准或外部写入。"

        case (.english, .stageCompose): "Compose"
        case (.english, .stageRoute): "Route review"
        case (.english, .stagePlan): "Plan"
        case (.english, .stageParallel): "Parallel work"
        case (.english, .stageApproval): "Approval"
        case (.english, .stageValidation): "Validation"
        case (.english, .stageResult): "Result"
        case (.english, .journeyPreview): "Task journey preview"
        case (.english, .syntheticGoal): "Preview goal"
        case (.english, .routeHeadline): "Review how Forma AI will approach this task"
        case (.english, .routeBody): "A local route is preferred. Any capability gap or external action remains visible before you continue."
        case (.english, .routeLocalReason): "This content is suitable for processing on this Mac."
        case (.english, .routeCloudBoundary): "No cloud transmission and no silent model switch."
        case (.english, .planHeadline): "Turn the outcome into a plan you can supervise"
        case (.english, .planBody): "Every step has an owner and inspectable output. This synthetic plan creates no Agents."
        case (.english, .planResearch): "Collect and mark relevant material"
        case (.english, .planAnalyze): "Compare evidence and identify key findings"
        case (.english, .planDraft): "Create a reviewable result and evidence summary"
        case (.english, .parallelHeadline): "Three Agents collaborate in parallel with visible state"
        case (.english, .parallelBody): "This shows the responsibility, progress, and handoff shape of future execution. No process is running now."
        case (.english, .agentResearch): "Research Agent"
        case (.english, .agentAnalysis): "Analysis Agent"
        case (.english, .agentDraft): "Draft Agent"
        case (.english, .statusComplete): "Preview complete"
        case (.english, .statusRunningPreview): "Synthetic running state"
        case (.english, .statusQueuedPreview): "Waiting for upstream output"
        case (.english, .approvalHeadline): "Pause before an external action and show its scope"
        case (.english, .approvalBody): "This approval card shows the information a user will receive. It performs no approval and writes to no destination."
        case (.english, .approvalAction): "Proposed action"
        case (.english, .approvalScope): "Send the validated result summary"
        case (.english, .approvalDestination): "Destination"
        case (.english, .approvalDestinationValue): "Synthetic project workspace"
        case (.english, .approvalEffectLabel): "Effect"
        case (.english, .approvalEffect): "One-time external write with no standing permission"
        case (.english, .approvalPreviewOnly): "The next step only shows the after-approval Preview state."
        case (.english, .validationHeadline): "Check artifacts and evidence before presenting a result"
        case (.english, .validationBody): "Validation stays separate from generation so a generated output is never mistaken for task completion."
        case (.english, .artifactNotes): "Source notes"
        case (.english, .artifactBrief): "Reviewable brief"
        case (.english, .checkSources): "Source coverage"
        case (.english, .checkStructure): "Structural completeness"
        case (.english, .checkPrivacy): "Privacy boundary"
        case (.english, .valid): "Passed"
        case (.english, .resultHeadline): "Deliver the result, evidence, and unresolved items together"
        case (.english, .resultBody): "This synthetic result verifies the final reading order. It does not mean a real model or Agent completed the task."
        case (.english, .resultSummary): "A structured brief now presents key findings, supporting evidence, and recommended next steps."
        case (.english, .resultEvidence): "2 synthetic artifacts · 3 validations passed"
        case (.english, .resultUnresolved): "Unresolved items"
        case (.english, .none): "None"
        case (.english, .nextPreview): "Show next preview state"
        case (.english, .showApprovedPreview): "Show after-approval state"
        case (.english, .showValidationPreview): "Show validation state"
        case (.english, .showResultPreview): "Show result state"
        case (.english, .backToEdit): "Back to editing"
        case (.english, .previewStateNotice): "Every state is deterministic synthetic data. No task, approval, or external write is performed."
        }
    }

    func stageTitle(_ stage: PreviewTransitionStage) -> String {
        switch stage {
        case .compose: self[.stageCompose]
        case .routeReview: self[.stageRoute]
        case .plan: self[.stagePlan]
        case .parallelExecution: self[.stageParallel]
        case .approval: self[.stageApproval]
        case .validation: self[.stageValidation]
        case .result: self[.stageResult]
        }
    }
}
