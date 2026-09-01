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
        }
    }
}
