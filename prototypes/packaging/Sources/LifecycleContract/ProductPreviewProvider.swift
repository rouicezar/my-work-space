public enum PreviewTaskState: String, CaseIterable, Sendable, Hashable {
    case empty
    case completed
    case blocked
    case partial
    case approvalRequired
    case interrupted
    case memoryReview
    case unavailable
}

public enum PreviewRoute: String, Sendable, Equatable {
    case local
    case localParallel
    case cloudProposal
    case governedMemory
    case unavailable
}

public enum PreviewAgentState: String, Sendable, Equatable {
    case queued
    case running
    case blocked
    case completed
}

public enum PreviewApprovalState: String, Sendable, Equatable {
    case required
    case approved
    case declined
}

public enum PreviewInteraction: String, Sendable, Equatable {
    case none
    case showNextPreviewState
}

public enum PreviewDisclosurePlacement: Sendable, Equatable {
    case persistentTopBanner
}

public enum PreviewWorkspaceSection: Sendable, Equatable {
    case goalAndRoute
    case executionRail
    case parallelAgents
    case approvalScope
    case artifactsAndValidation
    case resultAndUnresolvedEvidence
}

public struct PreviewWorkspaceSurfaceContract: Sendable {
    public let developmentLaunchArgument: String
    public let productionDefaultsToRuntime: Bool
    public let disclosurePlacement: PreviewDisclosurePlacement
    public let sections: [PreviewWorkspaceSection]
    public let runtimeActionsAllowed: Bool

    public static let productDefault = PreviewWorkspaceSurfaceContract(
        developmentLaunchArgument: "--product-preview",
        productionDefaultsToRuntime: true,
        disclosurePlacement: .persistentTopBanner,
        sections: [
            .goalAndRoute,
            .executionRail,
            .parallelAgents,
            .approvalScope,
            .artifactsAndValidation,
            .resultAndUnresolvedEvidence,
        ],
        runtimeActionsAllowed: false
    )
}

public enum FirstRunStep: String, CaseIterable, Sendable, Equatable {
    case welcome
    case privacy
    case prepareLocalAI
    case recommendedModel
    case macOSPermissions
    case optionalCloud
    case createFirstTask
}

public enum ProductLanguage: String, CaseIterable, Sendable, Equatable, Identifiable {
    case simplifiedChinese
    case english

    public var id: String { rawValue }
}

public enum FirstRunLanguageSelection: Sendable, Equatable {
    case requiredBeforeOnboarding
}

public struct FirstRunSurfaceContract: Sendable {
    public let developmentLaunchArgument: String
    public let productionAppearsOnlyWhenOnboardingIsIncomplete: Bool
    public let steps: [FirstRunStep]
    public let languageSelection: FirstRunLanguageSelection
    public let supportedLanguages: [ProductLanguage]
    public let localPreparationIsProductManaged: Bool
    public let requiresManualTerminalSetup: Bool
    public let exposesUpstreamProjectNamesToNovices: Bool

    public static let productDefault = FirstRunSurfaceContract(
        developmentLaunchArgument: "--first-run-preview",
        productionAppearsOnlyWhenOnboardingIsIncomplete: true,
        steps: FirstRunStep.allCases,
        languageSelection: .requiredBeforeOnboarding,
        supportedLanguages: [.simplifiedChinese, .english],
        localPreparationIsProductManaged: true,
        requiresManualTerminalSetup: false,
        exposesUpstreamProjectNamesToNovices: false
    )
}

public enum DailyWorkbenchSection: Sendable, Equatable {
    case primaryNavigation
    case recentTasks
    case newTaskComposer
    case routeAndPrivacy
    case contextAttachments
    case supervisionRail
}

public struct DailyWorkbenchSurfaceContract: Sendable {
    public let developmentLaunchArgument: String
    public let productionDefaultsToRuntime: Bool
    public let sections: [DailyWorkbenchSection]
    public let supportedLanguages: [ProductLanguage]
    public let languageSwitchIsVisible: Bool
    public let supervisionRailIsCollapsible: Bool
    public let runtimeActionsAllowed: Bool
    public let readsAttachmentContents: Bool
    public let persistsPreviewHistory: Bool

    public static let productDefault = DailyWorkbenchSurfaceContract(
        developmentLaunchArgument: "--daily-workbench-preview",
        productionDefaultsToRuntime: true,
        sections: [
            .primaryNavigation,
            .recentTasks,
            .newTaskComposer,
            .routeAndPrivacy,
            .contextAttachments,
            .supervisionRail,
        ],
        supportedLanguages: [.simplifiedChinese, .english],
        languageSwitchIsVisible: true,
        supervisionRailIsCollapsible: true,
        runtimeActionsAllowed: false,
        readsAttachmentContents: false,
        persistsPreviewHistory: false
    )
}

public enum PreviewTransitionStage: String, CaseIterable, Sendable, Equatable, Identifiable {
    case compose
    case routeReview
    case plan
    case parallelExecution
    case approval
    case validation
    case result

    public var id: String { rawValue }
}

public struct ComposeToExecutionPreviewContract: Sendable {
    public let stages: [PreviewTransitionStage]
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let languageSwitchPreservesStage: Bool
    public let runtimeActionsAllowed: Bool
    public let performsApproval: Bool
    public let persistsState: Bool

    public static let productDefault = ComposeToExecutionPreviewContract(
        stages: PreviewTransitionStage.allCases,
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        languageSwitchPreservesStage: true,
        runtimeActionsAllowed: false,
        performsApproval: false,
        persistsState: false
    )
}

public enum HistoryPreviewTaskState: String, CaseIterable, Sendable, Equatable, Identifiable {
    case interrupted
    case blocked
    case failed
    case partial
    case cancelled
    case completed
    case unknown

    public var id: String { rawValue }
}

public enum HistoryRecoverySection: Sendable, Equatable {
    case taskList
    case taskDetail
    case executionSummary
    case recoveryDecision
    case auditBoundary
}


public struct TaskMetadataProjectionContract: Sendable, Equatable {
    public let schemaVersion: Int
    public let runtimeAuthority: String
    public let productOwnedFields: [String]
    public let forbiddenMetadataClaims: [String]
    public let terminalRuntimeStates: [String]
    public let resumableRuntimeStates: [String]

    public static let productDefault = TaskMetadataProjectionContract(
        schemaVersion: 1,
        runtimeAuthority: "herdr",
        productOwnedFields: [
            "task_id", "correlation_id", "run_id", "intent_label",
            "herdr_pane_id", "herdr_workspace_id", "herdr_tab_id", "herdr_terminal_id",
            "last_accepted_revision", "approval_refs", "artifact_refs",
            "policy_preview_digest", "recorded_at", "updated_at",
        ],
        forbiddenMetadataClaims: [
            "completed", "succeeded", "failed", "cancelled", "resumable",
            "runtime_state", "runtime_phase", "agent_status", "may_resume",
            "is_terminal", "display_outcome",
        ],
        terminalRuntimeStates: ["succeeded", "failed", "cancelled"],
        resumableRuntimeStates: ["interrupted", "blocked", "failed", "unknown"]
    )
}

public struct HistoryRecoveryPreviewContract: Sendable {
    public let states: [HistoryPreviewTaskState]
    public let sections: [HistoryRecoverySection]
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let languageSwitchPreservesSelection: Bool
    public let readsPersistedHistory: Bool
    public let runtimeActionsAllowed: Bool
    public let performsResume: Bool
    public let performsRetry: Bool
    public let performsCancellation: Bool
    public let performsForceTermination: Bool

    public static let productDefault = HistoryRecoveryPreviewContract(
        states: HistoryPreviewTaskState.allCases,
        sections: [
            .taskList,
            .taskDetail,
            .executionSummary,
            .recoveryDecision,
            .auditBoundary,
        ],
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        languageSwitchPreservesSelection: true,
        readsPersistedHistory: false,
        runtimeActionsAllowed: false,
        performsResume: false,
        performsRetry: false,
        performsCancellation: false,
        performsForceTermination: false
    )

    public static let metadataProjection = TaskMetadataProjectionContract.productDefault
}

public enum GovernedMemoryReviewState: String, CaseIterable, Sendable, Equatable, Hashable, Identifiable {
    case candidate
    case confirmed
    case conflict
    case correction
    case deleted

    public var id: String { rawValue }
}

public enum GovernedMemoryReviewSection: Sendable, Equatable {
    case recordList
    case recordDetail
    case provenance
    case authorityBoundary
}


public struct GovernedMemoryReviewRoute: Sendable, Equatable {
    public let method: String
    public let path: String
    public let supervisorCommand: String?

    public init(method: String, path: String, supervisorCommand: String?) {
        self.method = method
        self.path = path
        self.supervisorCommand = supervisorCommand
    }
}

public struct GovernedMemoryReviewUIFieldMap: Sendable, Equatable {
    public let primaryID: String
    public let status: String
    public let claimKey: String
    public let content: String
    public let correlationID: String
    public let sources: String
    public let semanticaID: String?
    public let recordID: String?
    public let version: String?
    public let previousRecordID: String?

    public init(
        primaryID: String,
        status: String,
        claimKey: String,
        content: String,
        correlationID: String,
        sources: String,
        semanticaID: String?,
        recordID: String?,
        version: String?,
        previousRecordID: String?
    ) {
        self.primaryID = primaryID
        self.status = status
        self.claimKey = claimKey
        self.content = content
        self.correlationID = correlationID
        self.sources = sources
        self.semanticaID = semanticaID
        self.recordID = recordID
        self.version = version
        self.previousRecordID = previousRecordID
    }
}

public struct GovernedMemoryReviewServiceBinding: Sendable, Equatable {
    public let loopbackPort: Int
    public let auditPath: String
    public let confirmedAuthority: String
    public let snapshotCommand: String
    public let confirmCommand: String
    public let rejectCommand: String
    public let routes: [String: GovernedMemoryReviewRoute]
    public let uiStateFields: [GovernedMemoryReviewState: GovernedMemoryReviewUIFieldMap]

    public static let productDefault = GovernedMemoryReviewServiceBinding(
        loopbackPort: 43111,
        auditPath: "logs/audit/memory-review.jsonl",
        confirmedAuthority: "semantica",
        snapshotCommand: "memory-review-snapshot",
        confirmCommand: "memory-review-confirm",
        rejectCommand: "memory-review-reject",
        routes: [
            "health": GovernedMemoryReviewRoute(method: "GET", path: "/v1/memory/health", supervisorCommand: nil),
            "list_candidates": GovernedMemoryReviewRoute(method: "POST", path: "/v1/memory/candidates", supervisorCommand: "memory-review-snapshot"),
            "get_candidate": GovernedMemoryReviewRoute(method: "POST", path: "/v1/memory/candidate/get", supervisorCommand: nil),
            "confirm": GovernedMemoryReviewRoute(method: "POST", path: "/v1/memory/confirm", supervisorCommand: "memory-review-confirm"),
            "reject": GovernedMemoryReviewRoute(method: "POST", path: "/v1/memory/reject", supervisorCommand: "memory-review-reject"),
            "export": GovernedMemoryReviewRoute(method: "POST", path: "/v1/memory/export", supervisorCommand: nil),
            "get": GovernedMemoryReviewRoute(method: "POST", path: "/v1/memory/get", supervisorCommand: nil),
        ],
        uiStateFields: [
            .candidate: GovernedMemoryReviewUIFieldMap(
                primaryID: "candidate_id", status: "pending", claimKey: "claim_key", content: "content",
                correlationID: "correlation_id", sources: "sources",
                semanticaID: nil, recordID: nil, version: nil, previousRecordID: nil
            ),
            .confirmed: GovernedMemoryReviewUIFieldMap(
                primaryID: "record_id", status: "confirmed", claimKey: "claim_key", content: "content",
                correlationID: "correlation_id", sources: "sources",
                semanticaID: "semantica_id", recordID: "record_id", version: "version", previousRecordID: "previous_record_id"
            ),
            .conflict: GovernedMemoryReviewUIFieldMap(
                primaryID: "candidate_id", status: "conflict", claimKey: "claim_key", content: "content",
                correlationID: "correlation_id", sources: "sources",
                semanticaID: nil, recordID: nil, version: nil, previousRecordID: nil
            ),
            .correction: GovernedMemoryReviewUIFieldMap(
                primaryID: "record_id", status: "confirmed", claimKey: "claim_key", content: "content",
                correlationID: "correlation_id", sources: "sources",
                semanticaID: "semantica_id", recordID: "record_id", version: "version", previousRecordID: "previous_record_id"
            ),
            .deleted: GovernedMemoryReviewUIFieldMap(
                primaryID: "record_id", status: "deleted", claimKey: "claim_key", content: "content",
                correlationID: "correlation_id", sources: "sources",
                semanticaID: "semantica_id", recordID: "record_id", version: "version", previousRecordID: "previous_record_id"
            ),
        ]
    )
}

public struct GovernedMemoryReviewContract: Sendable {
    public let states: [GovernedMemoryReviewState]
    public let sections: [GovernedMemoryReviewSection]
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let languageSwitchPreservesSelection: Bool
    public let readsPersistentMemory: Bool
    public let runtimeActionsAllowed: Bool
    public let performsPromote: Bool
    public let performsCorrect: Bool
    public let performsDelete: Bool

    public static let productDefault = GovernedMemoryReviewContract(
        states: GovernedMemoryReviewState.allCases,
        sections: [
            .recordList,
            .recordDetail,
            .provenance,
            .authorityBoundary,
        ],
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        languageSwitchPreservesSelection: true,
        readsPersistentMemory: false,
        runtimeActionsAllowed: false,
        performsPromote: false,
        performsCorrect: false,
        performsDelete: false
    )

    public static let realServiceBinding = GovernedMemoryReviewServiceBinding.productDefault
}

public enum AgentAdapterKind: String, CaseIterable, Sendable, Equatable, Hashable, Identifiable {
    case herdrTerminal
    case codexCompatible
    case claudeCompatible
    case holaOSReference

    public var id: String { rawValue }
}

public enum AgentsToolsSection: Sendable, Equatable {
    case agentList
    case agentDetail
    case requiredOperations
    case authorityBoundary
}

public struct AgentsToolsContract: Sendable {
    public let agentKinds: [AgentAdapterKind]
    public let requiredOperations: [String]
    public let sections: [AgentsToolsSection]
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let languageSwitchPreservesSelection: Bool
    public let runtimeActionsAllowed: Bool
    public let performsDispatch: Bool
    public let reimplementsUpstream: Bool

    public static let productDefault = AgentsToolsContract(
        agentKinds: AgentAdapterKind.allCases,
        requiredOperations: ["discover", "dispatch", "status", "handoff", "cancel", "resume", "artifacts", "audit"],
        sections: [.agentList, .agentDetail, .requiredOperations, .authorityBoundary],
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        languageSwitchPreservesSelection: true,
        runtimeActionsAllowed: false,
        performsDispatch: false,
        reimplementsUpstream: false
    )
}

public enum PermissionScope: String, CaseIterable, Sendable, Equatable, Hashable, Identifiable {
    case read
    case write
    case send
    case delete
    case execute
    case credential

    public var id: String { rawValue }
}

public enum PermissionsSection: Sendable, Equatable {
    case scopeList
    case scopeDetail
    case approvalPolicy
    case authorityBoundary
}

public struct PermissionsContract: Sendable {
    public let scopes: [PermissionScope]
    public let sections: [PermissionsSection]
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let languageSwitchPreservesSelection: Bool
    public let runtimeActionsAllowed: Bool
    public let performsApproval: Bool
    public let grantsPermission: Bool

    public static let productDefault = PermissionsContract(
        scopes: PermissionScope.allCases,
        sections: [.scopeList, .scopeDetail, .approvalPolicy, .authorityBoundary],
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        languageSwitchPreservesSelection: true,
        runtimeActionsAllowed: false,
        performsApproval: false,
        grantsPermission: false
    )
}

public enum ModelRouteState: String, CaseIterable, Sendable, Equatable, Hashable, Identifiable {
    case automaticLocalFirst
    case localOnly
    case cloudWithApproval

    public var id: String { rawValue }
}

public struct ModelsProvidersContract: Sendable {
    public let routeStates: [ModelRouteState]
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let runtimeActionsAllowed: Bool
    public let downloadsModel: Bool
    public let cloudDisabledByDefault: Bool

    public static let productDefault = ModelsProvidersContract(
        routeStates: ModelRouteState.allCases,
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        runtimeActionsAllowed: false,
        downloadsModel: false,
        cloudDisabledByDefault: true
    )
}

public enum RuntimeFinalState: String, CaseIterable, Sendable, Equatable, Hashable, Identifiable {
    case stopped
    case starting
    case running
    case degraded
    case failed

    public var id: String { rawValue }
}

public struct LocalRuntimeContract: Sendable {
    public let states: [RuntimeFinalState]
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let runtimeActionsAllowed: Bool
    public let startsRuntime: Bool
    public let reportsHonestState: Bool

    public static let productDefault = LocalRuntimeContract(
        states: RuntimeFinalState.allCases,
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        runtimeActionsAllowed: false,
        startsRuntime: false,
        reportsHonestState: true
    )
}

public struct DataPrivacyContract: Sendable {
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let runtimeActionsAllowed: Bool
    public let storesSecretsInKeychain: Bool
    public let readsUserData: Bool

    public static let productDefault = DataPrivacyContract(
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        runtimeActionsAllowed: false,
        storesSecretsInKeychain: true,
        readsUserData: false
    )
}

public struct DiagnosticsRecoveryContract: Sendable {
    public let supportedLanguages: [ProductLanguage]
    public let allowedInteraction: PreviewInteraction
    public let runtimeActionsAllowed: Bool
    public let performsRecovery: Bool
    public let honestDegradation: Bool

    public static let productDefault = DiagnosticsRecoveryContract(
        supportedLanguages: [.simplifiedChinese, .english],
        allowedInteraction: .showNextPreviewState,
        runtimeActionsAllowed: false,
        performsRecovery: false,
        honestDegradation: true
    )
}

public struct PreviewAgent: Identifiable, Sendable, Equatable {
    public let id: String
    public let role: String
    public let state: PreviewAgentState
    public let summary: String
}

public struct PreviewApproval: Identifiable, Sendable, Equatable {
    public let id: String
    public let title: String
    public let scope: String
    public let state: PreviewApprovalState
    public let allowedInteraction: PreviewInteraction
}

public struct PreviewArtifact: Identifiable, Sendable, Equatable {
    public let id: String
    public let title: String
    public let validation: String
}

public struct PreviewTaskPresentation: Identifiable, Sendable, Equatable {
    public let id: String
    public let goal: String
    public let route: PreviewRoute
    public let agents: [PreviewAgent]
    public let approvals: [PreviewApproval]
    public let artifacts: [PreviewArtifact]
    public let result: String?
    public let unresolvedItems: [String]
}

public struct ProductPreviewScenario: Identifiable, Sendable {
    public let schemaVersion: Int
    public let scenarioID: String
    public let title: String
    public let summary: String
    public let activeDestination: WorkbenchDestination
    public let state: PreviewTaskState
    public let task: PreviewTaskPresentation?
    public let history: [String]
    public let settings: [String]
    public let notice: String

    public var id: String { scenarioID }
}

/// Deterministic presentation data only. This type deliberately has no command clients,
/// external dependencies, persistence, or automatic runtime-fallback behavior.
public struct ProductPreviewProvider: Sendable {
    public static let isRuntimeFallbackAllowed = false
    public let notice = "Product Preview · synthetic data · no runtime action"
    public let scenarios: [ProductPreviewScenario]

    public init() {
        let disclosure = "Product Preview · synthetic data · no runtime action"
        scenarios = Self.makeScenarios(notice: disclosure)
    }

    public func scenario(id: String) -> ProductPreviewScenario? {
        scenarios.first { $0.scenarioID == id }
    }

    private static func makeScenarios(notice: String) -> [ProductPreviewScenario] {
        [
            scenario(
                "empty-workbench", "Start a private task",
                "Inspect the final empty workbench without user data.", .newTask, .empty,
                notice: notice
            ),
            scenario(
                "local-complete", "Completed locally",
                "Review evidence, validation, and a final local result.", .newTask, .completed,
                task: task("local-complete", route: .local,
                           agents: [agent("research", "Research", .completed)],
                           artifacts: [artifact("brief", "Validated brief", "Passed")],
                           result: "A validated sample result."),
                notice: notice
            ),
            scenario(
                "parallel-blocked", "Parallel work needs approval",
                "Supervise three upstream-shaped agents and one scoped approval.", .newTask, .blocked,
                task: task("parallel-blocked", route: .localParallel,
                           agents: [agent("research", "Research", .completed),
                                    agent("draft", "Draft", .running),
                                    agent("publish", "Publish", .blocked)],
                           approvals: [approval("publish", "Allow publishing", "One synthetic destination")]),
                notice: notice
            ),
            scenario(
                "partial-evidence", "Evidence is incomplete",
                "Keep valid artifacts visible without claiming completion.", .newTask, .partial,
                task: task("partial-evidence", route: .local,
                           artifacts: [artifact("notes", "Source notes", "Passed")],
                           unresolved: ["One source remains unverified"]),
                notice: notice
            ),
            scenario(
                "cloud-proposal", "Cloud proposal",
                "Preview the exact one-time transmission decision before anything is sent.", .newTask, .approvalRequired,
                task: task("cloud-proposal", route: .cloudProposal,
                           approvals: [approval("cloud", "Review cloud request",
                                                  "Synthetic prompt, model, location, and maximum cost")]),
                notice: notice
            ),
            scenario(
                "interrupted-recovery", "Interrupted task",
                "Compare reconciled resume and fresh-run choices as presentation only.", .history, .interrupted,
                task: task("interrupted-recovery", route: .localParallel,
                           unresolved: ["Runtime state must be reconciled before resume"]),
                history: ["preview-history-interrupted"],
                notice: notice
            ),
            scenario(
                "memory-governance", "Memory review",
                "Inspect candidate, confirmed, conflict, correction, and delete states.", .settings, .memoryReview,
                task: task("memory-governance", route: .governedMemory),
                settings: ["candidate", "confirmed", "conflict", "correction", "delete"],
                notice: notice
            ),
            scenario(
                "component-unavailable", "Capability unavailable",
                "Show an honest missing capability and recovery guidance.", .settings, .unavailable,
                task: task("component-unavailable", route: .unavailable,
                           unresolved: ["Required component is not available"]),
                settings: ["diagnostics", "recovery guidance"],
                notice: notice
            ),
        ]
    }

    private static func scenario(
        _ suffix: String,
        _ title: String,
        _ summary: String,
        _ destination: WorkbenchDestination,
        _ state: PreviewTaskState,
        task: PreviewTaskPresentation? = nil,
        history: [String] = [],
        settings: [String] = [],
        notice: String
    ) -> ProductPreviewScenario {
        ProductPreviewScenario(
            schemaVersion: 1, scenarioID: "preview-\(suffix)", title: title, summary: summary,
            activeDestination: destination, state: state, task: task,
            history: history, settings: settings, notice: notice
        )
    }

    private static func task(
        _ suffix: String,
        route: PreviewRoute,
        agents: [PreviewAgent] = [],
        approvals: [PreviewApproval] = [],
        artifacts: [PreviewArtifact] = [],
        result: String? = nil,
        unresolved: [String] = []
    ) -> PreviewTaskPresentation {
        PreviewTaskPresentation(
            id: "preview-task-\(suffix)", goal: "Synthetic goal for \(suffix)", route: route,
            agents: agents, approvals: approvals, artifacts: artifacts, result: result,
            unresolvedItems: unresolved
        )
    }

    private static func agent(_ suffix: String, _ role: String, _ state: PreviewAgentState) -> PreviewAgent {
        PreviewAgent(id: "preview-agent-\(suffix)", role: role, state: state, summary: "Synthetic \(role.lowercased()) status")
    }

    private static func approval(_ suffix: String, _ title: String, _ scope: String) -> PreviewApproval {
        PreviewApproval(id: "preview-approval-\(suffix)", title: title, scope: scope, state: .required, allowedInteraction: .showNextPreviewState)
    }

    private static func artifact(_ suffix: String, _ title: String, _ validation: String) -> PreviewArtifact {
        PreviewArtifact(id: "preview-artifact-\(suffix)", title: title, validation: validation)
    }
}
