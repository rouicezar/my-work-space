import LifecycleContract

enum ModelsProvidersCopyKey {
    case modelsProvidersTitle, modelsProvidersSyntheticOnly, modelsProvidersPreviewBadge
    case modelsProvidersBoundary, modelsProvidersBoundaryBody
}

enum LocalRuntimeCopyKey {
    case localRuntimeTitle, localRuntimeSyntheticOnly, localRuntimePreviewBadge
    case localRuntimeBoundary, localRuntimeBoundaryBody
}

enum DataPrivacyCopyKey {
    case dataPrivacyTitle, dataPrivacySyntheticOnly, dataPrivacyPreviewBadge
    case dataPrivacyBoundary, dataPrivacyBoundaryBody
}

enum DiagnosticsCopyKey {
    case diagnosticsTitle, diagnosticsSyntheticOnly, diagnosticsPreviewBadge
    case diagnosticsBoundary, diagnosticsBoundaryBody
}

extension ProductCopy {
    subscript(key: ModelsProvidersCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .modelsProvidersTitle): "模型与提供商"
        case (.simplifiedChinese, .modelsProvidersSyntheticOnly): "3 个合成路由状态，用于检查最终产品如何呈现模型路由与云端开关。"
        case (.simplifiedChinese, .modelsProvidersPreviewBadge): "预览样例"
        case (.simplifiedChinese, .modelsProvidersBoundary): "模型路由边界"
        case (.simplifiedChinese, .modelsProvidersBoundaryBody):
            "本地优先是默认；云端仅在用户配置后可用，且每次传输都需预览与逐次批准。"
            + "此预览绝不下载模型或发起云端调用。"
        case (.english, .modelsProvidersTitle): "Models & Providers"
        case (.english, .modelsProvidersSyntheticOnly): "Three synthetic route states for reviewing how the finished product presents model routing and the cloud switch."
        case (.english, .modelsProvidersPreviewBadge): "PREVIEW EXAMPLE"
        case (.english, .modelsProvidersBoundary): "Model routing boundary"
        case (.english, .modelsProvidersBoundaryBody):
            "Local-first is the default; cloud becomes available only after user configuration, "
            + "and every transmission requires preview and per-request approval. "
            + "This preview never downloads a model or makes a cloud call."
        }
    }

    subscript(key: LocalRuntimeCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .localRuntimeTitle): "本地运行时"
        case (.simplifiedChinese, .localRuntimeSyntheticOnly): "5 个合成运行时状态，用于检查最终产品如何诚实呈现本地运行时状态。"
        case (.simplifiedChinese, .localRuntimePreviewBadge): "预览样例"
        case (.simplifiedChinese, .localRuntimeBoundary): "运行时诚实边界"
        case (.simplifiedChinese, .localRuntimeBoundaryBody):
            "健康端点不能代替推理证据。缺失能力绝不显示为空成功；"
            + "此预览不启动或停止任何运行时。"
        case (.english, .localRuntimeTitle): "Local Runtime"
        case (.english, .localRuntimeSyntheticOnly): "Five synthetic runtime states for reviewing how the finished product honestly presents the local runtime state."
        case (.english, .localRuntimePreviewBadge): "PREVIEW EXAMPLE"
        case (.english, .localRuntimeBoundary): "Runtime honesty boundary"
        case (.english, .localRuntimeBoundaryBody):
            "A health endpoint is not inference proof. Missing capability never appears "
            + "as an empty success; this preview starts or stops no runtime."
        }
    }

    subscript(key: DataPrivacyCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .dataPrivacyTitle): "数据与隐私"
        case (.simplifiedChinese, .dataPrivacySyntheticOnly): "合成隐私说明，用于检查最终产品如何呈现本地优先与密钥边界。"
        case (.simplifiedChinese, .dataPrivacyPreviewBadge): "预览样例"
        case (.simplifiedChinese, .dataPrivacyBoundary): "隐私边界"
        case (.simplifiedChinese, .dataPrivacyBoundaryBody):
            "本地执行优先；凭据仅存 Keychain；审计记录绝不包含密钥值。"
            + "此预览不读取任何用户数据。"
        case (.english, .dataPrivacyTitle): "Data & Privacy"
        case (.english, .dataPrivacySyntheticOnly): "A synthetic privacy statement for reviewing how the finished product presents local-first and secret boundaries."
        case (.english, .dataPrivacyPreviewBadge): "PREVIEW EXAMPLE"
        case (.english, .dataPrivacyBoundary): "Privacy boundary"
        case (.english, .dataPrivacyBoundaryBody):
            "Local execution is preferred; credentials live only in Keychain; audit records "
            + "never contain secret values. This preview reads no user data."
        }
    }

    subscript(key: DiagnosticsCopyKey) -> String {
        switch (language, key) {
        case (.simplifiedChinese, .diagnosticsTitle): "诊断与恢复"
        case (.simplifiedChinese, .diagnosticsSyntheticOnly): "合成诊断说明，用于检查最终产品如何呈现诚实降级与恢复。"
        case (.simplifiedChinese, .diagnosticsPreviewBadge): "预览样例"
        case (.simplifiedChinese, .diagnosticsBoundary): "诊断与恢复边界"
        case (.simplifiedChinese, .diagnosticsBoundaryBody):
            "组件健康与工作流健康分开报告；恢复是显式动作，从不静默降级。"
            + "此预览不执行任何恢复。"
        case (.english, .diagnosticsTitle): "Diagnostics & Recovery"
        case (.english, .diagnosticsSyntheticOnly): "A synthetic diagnostics statement for reviewing how the finished product presents honest degradation and recovery."
        case (.english, .diagnosticsPreviewBadge): "PREVIEW EXAMPLE"
        case (.english, .diagnosticsBoundary): "Diagnostics and recovery boundary"
        case (.english, .diagnosticsBoundaryBody):
            "Component health and workflow health are reported separately; recovery is an "
            + "explicit action, never silent degradation. This preview performs no recovery."
        }
    }

    func modelRouteTitle(_ state: ModelRouteState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .automaticLocalFirst): "自动本地优先"
        case (.simplifiedChinese, .localOnly): "仅本地"
        case (.simplifiedChinese, .cloudWithApproval): "云端需批准"
        case (.english, .automaticLocalFirst): "Automatic local-first"
        case (.english, .localOnly): "Local only"
        case (.english, .cloudWithApproval): "Cloud with approval"
        }
    }

    func modelRouteDetail(_ state: ModelRouteState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .automaticLocalFirst): "默认在本地运行；只有本地能力边界明确且经批准时才提议云端。"
        case (.simplifiedChinese, .localOnly): "仅使用本地模型；即使超出能力边界也不发起云端调用。"
        case (.simplifiedChinese, .cloudWithApproval): "每次云端传输都需要预览、成本估算与逐次批准。"
        case (.english, .automaticLocalFirst): "Runs locally by default; proposes cloud only when the local capability boundary is clear and approved."
        case (.english, .localOnly): "Uses only the local model; never makes a cloud call even past the capability boundary."
        case (.english, .cloudWithApproval): "Every cloud transmission requires preview, cost estimate, and per-request approval."
        }
    }

    func runtimeStateTitle(_ state: RuntimeFinalState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .stopped): "已停止"
        case (.simplifiedChinese, .starting): "启动中"
        case (.simplifiedChinese, .running): "运行中"
        case (.simplifiedChinese, .degraded): "需恢复"
        case (.simplifiedChinese, .failed): "已失败"
        case (.english, .stopped): "Stopped"
        case (.english, .starting): "Starting"
        case (.english, .running): "Running"
        case (.english, .degraded): "Needs recovery"
        case (.english, .failed): "Failed"
        }
    }

    func runtimeStateDetail(_ state: RuntimeFinalState) -> String {
        switch (language, state) {
        case (.simplifiedChinese, .stopped): "本地运行时未启动；尚未证明推理。"
        case (.simplifiedChinese, .starting): "正在启动 oMLX、加载模型并校验 Broker。"
        case (.simplifiedChinese, .running): "运行时与策略 Broker 已运行；仍需真实 completion/embedding 证明推理。"
        case (.simplifiedChinese, .degraded): "运行时需要恢复；诚实报告受损能力。"
        case (.simplifiedChinese, .failed): "运行时动作已安全失败；绝不伪装为成功。"
        case (.english, .stopped): "The local runtime is not started; inference is not yet proven."
        case (.english, .starting): "Starting oMLX, loading the model, and verifying the Broker."
        case (.english, .running): "Runtime and policy Broker are running; inference still needs a real completion/embedding proof."
        case (.english, .degraded): "The runtime needs recovery; degraded capability is reported honestly."
        case (.english, .failed): "A runtime action failed safely; it is never presented as success."
        }
    }
}
