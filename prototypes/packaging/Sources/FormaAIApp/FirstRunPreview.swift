import SwiftUI
import LifecycleContract

struct FirstRunPreview: View {
    private let contract = FirstRunSurfaceContract.productDefault
    @State private var language: ProductLanguage?
    @State private var selectedStep: FirstRunStep = .welcome

    var body: some View {
        VStack(spacing: 0) {
            previewDisclosure

            if let language {
                onboarding(language: language)
            } else {
                languageSelection
            }
        }
        .frame(minWidth: 980, minHeight: 650)
    }

    private var previewDisclosure: some View {
        HStack {
            Label("Product Preview · 产品预览 · synthetic data · no runtime action", systemImage: "eye.trianglebadge.exclamationmark")
                .font(.callout.weight(.semibold))
            Spacer()
        }
        .padding(.horizontal, 20).padding(.vertical, 10)
        .background(Color(red: 0.96, green: 0.76, blue: 0.22))
        .foregroundStyle(.black.opacity(0.78))
    }

    private var languageSelection: some View {
        VStack(spacing: 28) {
            Spacer()
            Image(systemName: "sparkles.rectangle.stack.fill")
                .font(.system(size: 48)).foregroundStyle(.blue)
            VStack(spacing: 10) {
                Text("欢迎使用 Forma AI").font(.system(size: 34, weight: .semibold, design: .rounded))
                Text("Welcome to Forma AI").font(.title2.weight(.medium))
                Text("请选择语言 · Choose your language")
                    .font(.title3).foregroundStyle(.secondary)
            }
            HStack(spacing: 18) {
                languageButton(.simplifiedChinese, title: "简体中文", subtitle: "继续使用中文")
                languageButton(.english, title: "English", subtitle: "Continue in English")
            }
            .frame(maxWidth: 640)
            Text("稍后可在设置中更改 · You can change this later in Settings")
                .font(.caption).foregroundStyle(.secondary)
            Spacer()
        }
        .padding(44).frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func languageButton(_ value: ProductLanguage, title: String, subtitle: String) -> some View {
        Button {
            language = value
            selectedStep = .welcome
        } label: {
            VStack(alignment: .leading, spacing: 10) {
                Image(systemName: "character.bubble.fill").font(.title2).foregroundStyle(.blue)
                Text(title).font(.title3.weight(.semibold))
                Text(subtitle).font(.callout).foregroundStyle(.secondary)
            }
            .padding(20).frame(maxWidth: .infinity, minHeight: 140, alignment: .topLeading)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(.blue.opacity(0.35), lineWidth: 1.5))
        }
        .buttonStyle(.plain)
    }

    private func onboarding(language: ProductLanguage) -> some View {
        let copy = FirstRunCopy(language: language)
        return HStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 28) {
                VStack(alignment: .leading, spacing: 8) {
                    Image(systemName: "sparkles.rectangle.stack.fill")
                        .font(.system(size: 30)).foregroundStyle(.blue)
                    Text("Forma AI").font(.title2.weight(.bold))
                    Text(copy.tagline).font(.callout).foregroundStyle(.secondary)
                }
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(contract.steps.enumerated()), id: \.element) { index, step in
                        Button { selectedStep = step } label: {
                            HStack(spacing: 12) {
                                Text("\(index + 1)").font(.caption.monospaced().weight(.bold))
                                    .frame(width: 24, height: 24)
                                    .background(selectedStep == step ? Color.blue : Color.secondary.opacity(0.13), in: Circle())
                                    .foregroundStyle(selectedStep == step ? .white : .secondary)
                                Text(copy.title(for: step)).font(.callout.weight(selectedStep == step ? .semibold : .regular))
                                Spacer()
                            }
                            .padding(.vertical, 8).padding(.horizontal, 10).contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                    }
                }
                Spacer()
                Button(copy.changeLanguage) { self.language = nil }
                    .buttonStyle(.plain).font(.caption).foregroundStyle(.secondary)
            }
            .padding(30).frame(width: 300).background(.thinMaterial)

            Divider()

            VStack(alignment: .leading, spacing: 26) {
                Spacer()
                Text(copy.eyebrow(for: selectedStep)).font(.caption.monospaced().weight(.bold)).foregroundStyle(.blue)
                Text(copy.headline(for: selectedStep))
                    .font(.system(size: 36, weight: .semibold, design: .rounded))
                    .frame(maxWidth: 650, alignment: .leading)
                Text(copy.explanation(for: selectedStep))
                    .font(.title3).foregroundStyle(.secondary)
                    .frame(maxWidth: 650, alignment: .leading)
                HStack(spacing: 12) {
                    readinessCard(copy.privateByDefault, "lock.shield.fill", .green)
                    readinessCard(copy.localAIManaged, "laptopcomputer.and.arrow.down", .blue)
                    readinessCard(copy.cloudOptional, "cloud", .orange)
                }
                .frame(maxWidth: 720)
                Spacer()
                HStack {
                    Text(copy.previewFootnote).font(.caption).foregroundStyle(.secondary)
                    Spacer()
                    Button(copy.primaryButton(for: selectedStep)) { advance() }
                        .buttonStyle(.borderedProminent)
                }
            }
            .padding(44).frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func readinessCard(_ title: String, _ symbol: String, _ color: Color) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Image(systemName: symbol).font(.title2).foregroundStyle(color)
            Text(title).font(.headline)
        }
        .padding(16).frame(maxWidth: .infinity, minHeight: 110, alignment: .topLeading)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 15))
        .overlay(RoundedRectangle(cornerRadius: 15).stroke(.separator.opacity(0.5)))
    }

    private func advance() {
        guard let index = contract.steps.firstIndex(of: selectedStep), index + 1 < contract.steps.count else { return }
        selectedStep = contract.steps[index + 1]
    }
}

private struct FirstRunCopy {
    let language: ProductLanguage
    private var zh: Bool { language == .simplifiedChinese }

    var tagline: String { zh ? "你的私密、本地优先 AI 工作台" : "Your private, local-first AI workbench" }
    var changeLanguage: String { zh ? "切换语言" : "Change language" }
    var privateByDefault: String { zh ? "默认保护隐私" : "Private by default" }
    var localAIManaged: String { zh ? "本地 AI 由产品管理" : "Local AI managed for you" }
    var cloudOptional: String { zh ? "云端始终可选" : "Cloud stays optional" }
    var previewFootnote: String { zh ? "产品预览不会下载、安装、发送或执行任何内容。" : "Nothing is downloaded, installed, sent, or executed in Product Preview." }

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
        case (.simplifiedChinese, .recommendedModel): "Forma AI 会根据这台 Mac 的可用内存和性能推荐均衡的本地配置，你可以稍后更改。"
        case (.simplifiedChinese, .macOSPermissions): "权限会在真实任务需要时逐步请求，而不是首次启动时一次性索取。"
        case (.simplifiedChinese, .optionalCloud): "只在你需要时添加云服务。凭据会受到保护，每次传输仍需你审核。"
        case (.simplifiedChinese, .createFirstTask): "用自然语言描述你想要的结果，Forma AI 会提出安全路径，并展示工作如何分配。"
        case (.english, .welcome): "Plan work, supervise parallel agents, review approvals, and keep evidence together in one native workbench."
        case (.english, .privacy): "Local routes are preferred. Before any cloud transmission or external write, you see the exact scope and decide."
        case (.english, .prepareLocalAI): "The product manages compatible local capabilities, versions, startup, repair, and removal. No separate upstream deployment is required."
        case (.english, .recommendedModel): "Forma AI recommends a balanced local profile from this Mac's available memory and performance. You can change it later."
        case (.english, .macOSPermissions): "Permissions are requested progressively, when a real task needs them—not as a blanket first-launch demand."
        case (.english, .optionalCloud): "Add a provider only if you want one. Credentials remain protected, and every transmission still requires review."
        case (.english, .createFirstTask): "Describe an outcome in plain language. Forma AI will propose a safe route and show how the work is divided."
        }
    }

    func primaryButton(for step: FirstRunStep) -> String {
        if zh { return step == .createFirstTask ? "创建第一个任务" : "继续" }
        return step == .createFirstTask ? "Create first task" : "Continue"
    }
}
