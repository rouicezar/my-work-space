import SwiftUI
import LifecycleContract
import SupervisorProtocol

enum SupervisorViewState: Sendable {
    case loading
    case unavailable(String)
    case ready(PreflightPayload)
}

struct InstallationContext: Sendable {
    let supervisor: URL
    let upstreams: URL
    let root: URL
}

struct ModelContext: Sendable {
    let supervisor: URL
    let root: URL
    let cacheRoot: URL
    let catalog: URL
}

enum InstallationViewState: Sendable {
    case loading
    case unavailable(String)
    case planned(InstallationPlanPayload)
    case installing(String)
    case installed(String)
    case failed(String)
}

enum ModelViewState: Sendable {
    case loading
    case unavailable(String)
    case planned(ModelPlanPayload)
    case linking
    case linked(String)
    case failed(String)
}

enum EmbeddingViewState: Sendable {
    case loading
    case planned(ModelPlanPayload)
    case downloading(Int64)
    case activating
    case active(String, Int)
    case failed(String)
}

enum RuntimeViewState: Sendable {
    case loading
    case stopped
    case starting
    case running
    case sampling
    case sample(String, String, String)
    case degraded(String)
    case failed(String)
}


extension ModelRouteChoice {
    var title: String {
        switch self {
        case .automaticLocalFirst: "Automatic · local first"
        case .localOnly: "Local only"
        case .cloudWithApproval: "Cloud · ask every time"
        }
    }

    var isExecutionBound: Bool {
        self == .automaticLocalFirst
    }

    var bindingStatus: String {
        switch self {
        case .automaticLocalFirst: "Ready"
        case .localOnly, .cloudWithApproval: "Execution binding pending"
        }
    }

    var safetyDescription: String {
        switch self {
        case .automaticLocalFirst:
            "Local by default. A cloud proposal never sends data until you approve the exact request."
        case .localOnly:
            "Local-only preference is saved for this task, but submission waits until the Supervisor routing contract accepts it."
        case .cloudWithApproval:
            "Cloud preference never authorizes sending. A credential, exact payload preview, and separate approval are still required; submission waits for routing-contract support."
        }
    }
}

extension LifecycleContract.SettingsSection {
    var title: String {
        switch self {
        case .general: "General"
        case .modelsAndProviders: "Models & Providers"
        case .agentsAndTools: "Agents & Tools"
        case .memory: "Memory"
        case .permissionsAndApprovals: "Permissions & Approvals"
        case .localRuntime: "Local Runtime"
        case .dataAndPrivacy: "Data & Privacy"
        case .diagnosticsAndRecovery: "Diagnostics & Recovery"
        }
    }

    var symbol: String {
        switch self {
        case .general: "gearshape"
        case .modelsAndProviders: "cpu"
        case .agentsAndTools: "rectangle.3.group"
        case .memory: "brain.head.profile"
        case .permissionsAndApprovals: "hand.raised"
        case .localRuntime: "server.rack"
        case .dataAndPrivacy: "lock.shield"
        case .diagnosticsAndRecovery: "stethoscope"
        }
    }

    var summary: String {
        switch self {
        case .general: "Everyday product preferences, separate from first-run setup."
        case .modelsAndProviders: "Local models, optional cloud providers, and truthful credential state."
        case .agentsAndTools: "Agent adapters, capabilities, and tool availability."
        case .memory: "Governed long-term memory and semantic retrieval."
        case .permissionsAndApprovals: "Review what agents may do and when Forma AI must ask."
        case .localRuntime: "Local inference status and runtime controls."
        case .dataAndPrivacy: "Data routes, retention, credentials, and audit boundaries."
        case .diagnosticsAndRecovery: "Progressively disclosed installation, repair, and component diagnostics."
        }
    }
}

enum WorkbenchTaskState: Sendable {
    case idle
    case submitting(String)
    case localResult(String, String, String)
    case cloudProposal(CloudProposalPayload)
    case cloudExecuting
    case cloudResult(String, String, Double, String)
    case denied
    case unavailable(String)
    case failed(String)

    var isBusy: Bool {
        if case .submitting = self { return true }
        return false
    }
}

enum AgentActivityViewState: Sendable {
    case loading
    case ready(RuntimePresentationState)
}

enum CloudSetupViewState: Sendable {
    case loading
    case disabled
    case enabled(String)
    case saving
    case failed(String)
}

struct TaskContext: Sendable {
    let supervisor: URL
    let root: URL
    let models: URL
    let hardware: URL
    let localProfiles: URL
    let cloud: URL
    let evidenceRoot: URL
}
