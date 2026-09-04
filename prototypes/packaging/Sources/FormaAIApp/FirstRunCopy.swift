import LifecycleContract

struct FirstRunCopy {
    let language: ProductLanguage
    private var zh: Bool { language == .simplifiedChinese }

    var tagline: String { zh ? "你的私密、本地优先 AI 工作台" : "Your private, local-first AI workbench" }
    var changeLanguage: String { zh ? "切换语言" : "Change language" }
    var privateByDefault: String { zh ? "默认保护隐私" : "Private by default" }
    var localAIManaged: String { zh ? "本地 AI 由产品管理" : "Local AI managed for you" }
    var cloudOptional: String { zh ? "云端始终可选" : "Cloud stays optional" }
    var previewFootnote: String {
        zh ? "产品预览不会下载、安装、发送或执行任何内容。" : "Nothing is downloaded, installed, sent, or executed in Product Preview."
    }
    var productionFootnote: String {
        zh ? "Forma AI 会在这台 Mac 上准备本地能力；任何云端使用都会先征求你的批准。" :
            "Forma AI prepares local capability on this Mac; any cloud use still requires your approval."
    }

    func title(for step: FirstRunStep) -> String {
        switch (language, step) {
        case (.simplifiedChinese, .welcome): "欢迎"
        case (.simplifiedChinese, .privacy): "隐私"
        case (.simplifiedChinese, .prepareLocalAI): "准备本地 AI"
        case (.simplifiedChinese, .recommendedModel): "推荐模型"
        case (.simplifiedChinese, .macOSPermissions): "macOS 权限"
        case (.simplifiedChinese, .optionalCloud): "可选云端"
        case (.simplifiedChinese, .createFirstTask): "第一个任务"
        case (.english, .welcome): "Welcome"
        case (.english, .privacy): "Privacy"
        case (.english, .prepareLocalAI): "Prepare local AI"
        case (.english, .recommendedModel): "Recommended model"
        case (.english, .macOSPermissions): "macOS permissions"
        case (.english, .optionalCloud): "Optional cloud"
        case (.english, .createFirstTask): "First task"
        }
    }

    func eyebrow(for step: FirstRunStep) -> String {
        let index = FirstRunStep.allCases.firstIndex(of: step)! + 1
        if zh { return step == .welcome ? "欢迎" : "第 \(index) 步，共 7 步" }
        return step == .welcome ? "WELCOME" : "STEP \(index) OF 7"
    }

    func headline(for step: FirstRunStep) -> String {
        switch (language, step) {
        case (.simplifiedChinese, .welcome): "一个应用，完成私密且可监督的 AI 工作。"
        case (.simplifiedChinese, .privacy): "除非你明确批准，否则工作内容只留在这台 Mac 上。"
        case (.simplifiedChinese, .prepareLocalAI): "Forma AI 会自动准备本地智能能力。"
        case (.simplifiedChinese, .recommendedModel): "从适合这台 Mac 的模型开始。"
        case (.simplifiedChinese, .macOSPermissions): "只授予每项任务真正需要的权限。"
        case (.simplifiedChinese, .optionalCloud): "云端模型始终可选，而且每次都会先询问。"
        case (.simplifiedChinese, .createFirstTask): "现在可以创建你的第一个任务了。"
        case (.english, .welcome): "One application for private, supervised AI work."
        case (.english, .privacy): "Your work stays on this Mac unless you approve otherwise."
        case (.english, .prepareLocalAI): "Forma AI prepares local intelligence automatically."
        case (.english, .recommendedModel): "Start with the model that fits this Mac."
        case (.english, .macOSPermissions): "Grant only the access each task genuinely needs."
        case (.english, .optionalCloud): "Cloud models are optional and always ask first."
        case (.english, .createFirstTask): "You are ready to create your first task."
        }
    }

    func explanation(for step: FirstRunStep) -> String {
        switch (language, step) {
        case (.simplifiedChinese, .welcome): "在一个原生工作台中规划任务、监督并行智能体、审核授权，并集中查看证据。"
        case (.simplifiedChinese, .privacy): "产品优先使用本地路径。任何云端传输或外部写入发生前，你都能看到准确范围并自行决定。"
        case (.simplifiedChinese, .prepareLocalAI): "产品负责兼容本地能力的版本、启动、修复与移除，无需你分别部署底层项目。"
        case (.simplifiedChinese, .recommendedModel): "Forma AI 会根据这台 Mac 的可用内存和性能推荐并准备均衡的本地配置，你可以稍后更改。"
        case (.simplifiedChinese, .macOSPermissions): "权限会在真实任务需要时逐步请求，而不是首次启动时一次性索取。"
        case (.simplifiedChinese, .optionalCloud): "只在你需要时添加云服务。凭据会受到保护，每次传输仍需你审核。"
        case (.simplifiedChinese, .createFirstTask): "用自然语言描述你想要的结果，Forma AI 会提出安全路径，并展示工作如何分配。"
        case (.english, .welcome): "Plan work, supervise parallel agents, review approvals, and keep evidence together in one native workbench."
        case (.english, .privacy): "Local routes are preferred. Before any cloud transmission or external write, you see the exact scope and decide."
        case (.english, .prepareLocalAI): "The product manages compatible local capabilities, versions, startup, repair, and removal. No separate upstream deployment is required."
        case (.english, .recommendedModel): "Forma AI recommends and prepares a balanced local profile from this Mac's available memory and performance. You can change it later."
        case (.english, .macOSPermissions): "Permissions are requested progressively, when a real task needs them—not as a blanket first-launch demand."
        case (.english, .optionalCloud): "Add a provider only if you want one. Credentials remain protected, and every transmission still requires review."
        case (.english, .createFirstTask): "Describe an outcome in plain language. Forma AI will propose a safe route and show how the work is divided."
        }
    }

    func primaryButton(for step: FirstRunStep, preparationBusy: Bool) -> String {
        if preparationBusy {
            return zh ? "正在准备…" : "Preparing…"
        }
        if zh { return step == .createFirstTask ? "进入工作台" : "继续" }
        return step == .createFirstTask ? "Enter workbench" : "Continue"
    }

    var firstRunRetry: String { zh ? "重试" : "Retry" }

    func preparationStatus(_ status: LocalAIPreparationStatus) -> String {
        switch (language, status) {
        case (.simplifiedChinese, .idle): "尚未开始准备本地 AI。"
        case (.simplifiedChinese, .planningRuntime): "正在检查本地运行时计划…"
        case (.simplifiedChinese, .installingRuntime): "正在下载并验证本地推理运行时…"
        case (.simplifiedChinese, .planningModel): "正在选择适合这台 Mac 的推荐模型…"
        case (.simplifiedChinese, .downloadingModel(let transferred, let total)): "正在下载本地模型… \(transferred)/\(total) 字节"
        case (.simplifiedChinese, .linkingModel): "正在准备模型引用…"
        case (.simplifiedChinese, .startingRuntime): "正在启动本地 AI 服务…"
        case (.simplifiedChinese, .ready): "本地 AI 已准备就绪。"
        case (.simplifiedChinese, .failed(let message)): "准备失败：\(message)"
        case (.english, .idle): "Local AI preparation has not started yet."
        case (.english, .planningRuntime): "Checking the local runtime plan…"
        case (.english, .installingRuntime): "Downloading and verifying the local inference runtime…"
        case (.english, .planningModel): "Selecting the recommended model for this Mac…"
        case (.english, .downloadingModel(let transferred, let total)): "Downloading the local model… \(transferred)/\(total) bytes"
        case (.english, .linkingModel): "Preparing the model reference…"
        case (.english, .startingRuntime): "Starting local AI services…"
        case (.english, .ready): "Local AI is ready."
        case (.english, .failed(let message)): "Preparation failed: \(message)"
        }
    }
}
