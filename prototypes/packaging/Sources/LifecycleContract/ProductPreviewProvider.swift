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
            scenario("empty-workbench", "Start a private task", "Inspect the final empty workbench without user data.", .newTask, .empty, notice: notice),
            scenario("local-complete", "Completed locally", "Review evidence, validation, and a final local result.", .newTask, .completed, task: task("local-complete", route: .local, agents: [agent("research", "Research", .completed)], artifacts: [artifact("brief", "Validated brief", "Passed")], result: "A validated sample result."), notice: notice),
            scenario("parallel-blocked", "Parallel work needs approval", "Supervise three upstream-shaped agents and one scoped approval.", .newTask, .blocked, task: task("parallel-blocked", route: .localParallel, agents: [agent("research", "Research", .completed), agent("draft", "Draft", .running), agent("publish", "Publish", .blocked)], approvals: [approval("publish", "Allow publishing", "One synthetic destination")]), notice: notice),
            scenario("partial-evidence", "Evidence is incomplete", "Keep valid artifacts visible without claiming completion.", .newTask, .partial, task: task("partial-evidence", route: .local, artifacts: [artifact("notes", "Source notes", "Passed")], unresolved: ["One source remains unverified"]), notice: notice),
            scenario("cloud-proposal", "Cloud proposal", "Preview the exact one-time transmission decision before anything is sent.", .newTask, .approvalRequired, task: task("cloud-proposal", route: .cloudProposal, approvals: [approval("cloud", "Review cloud request", "Synthetic prompt, model, location, and maximum cost")]), notice: notice),
            scenario("interrupted-recovery", "Interrupted task", "Compare reconciled resume and fresh-run choices as presentation only.", .history, .interrupted, task: task("interrupted-recovery", route: .localParallel, unresolved: ["Runtime state must be reconciled before resume"]), history: ["preview-history-interrupted"], notice: notice),
            scenario("memory-governance", "Memory review", "Inspect candidate, confirmed, conflict, correction, and delete states.", .settings, .memoryReview, task: task("memory-governance", route: .governedMemory), settings: ["candidate", "confirmed", "conflict", "correction", "delete"], notice: notice),
            scenario("component-unavailable", "Capability unavailable", "Show an honest missing capability and recovery guidance.", .settings, .unavailable, task: task("component-unavailable", route: .unavailable, unresolved: ["Required component is not available"]), settings: ["diagnostics", "recovery guidance"], notice: notice),
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
        ProductPreviewScenario(schemaVersion: 1, scenarioID: "preview-\(suffix)", title: title, summary: summary, activeDestination: destination, state: state, task: task, history: history, settings: settings, notice: notice)
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
        PreviewTaskPresentation(id: "preview-task-\(suffix)", goal: "Synthetic goal for \(suffix)", route: route, agents: agents, approvals: approvals, artifacts: artifacts, result: result, unresolvedItems: unresolved)
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
