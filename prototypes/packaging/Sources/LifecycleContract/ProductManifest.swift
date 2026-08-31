import Foundation

public enum WorkbenchDestination: Sendable {
    case newTask
    case history
    case settings
}

public enum ComposerPlacement: Sendable {
    case firstScreen
}

public enum TaskSubmissionBinding: Sendable {
    case supervisorUnifiedTask
}

public enum SetupAndRecoveryPlacement: Sendable {
    case separateSettings
}

public enum ModelSelectorPlacement: Sendable {
    case composerToolbar
}

public enum ModelRouteChoice: String, CaseIterable, Identifiable, Sendable {
    case automaticLocalFirst
    case localOnly
    case cloudWithApproval

    public var id: Self { self }
}

public enum CloudSelectionGuard: Sendable {
    case credentialAndPerRequestApproval
}

public struct ModelSelectionContract: Sendable {
    public let placement: ModelSelectorPlacement
    public let defaultChoice: ModelRouteChoice
    public let availableChoices: [ModelRouteChoice]
    public let cloudGuard: CloudSelectionGuard
}

public enum HistoryPlacement: Sendable, Equatable {
    case primaryNavigation
}

public enum HistorySource: Sendable, Equatable {
    case persistedTaskRecords
}

public enum HistoryEmptyState: Sendable, Equatable {
    case explicitNoHistory
}

public struct TaskHistoryContract: Sendable {
    public let placement: HistoryPlacement
    public let source: HistorySource
    public let emptyState: HistoryEmptyState
    public let previewFixturesAllowed: Bool
}

public enum RecoveryPlacement: Sendable, Equatable {
    case taskDetail
}

public enum RecoverableTaskState: Sendable, Equatable {
    case blocked
    case failed
    case interrupted
    case unknown
}

public enum ResumeSource: Sendable, Equatable {
    case persistedTaskAndVerifiedNativeSession
}

public enum RecoveryReconciliation: Sendable, Equatable {
    case freshSnapshotAndRevisionBeforeResume
}

public enum ForceTerminationPolicy: Sendable, Equatable {
    case separateExplicitApproval
}

public struct TaskRecoveryContract: Sendable {
    public let placement: RecoveryPlacement
    public let visibleStates: [RecoverableTaskState]
    public let resumeSource: ResumeSource
    public let reconciliation: RecoveryReconciliation
    public let forceTermination: ForceTerminationPolicy
}

public struct WorkbenchSurfaceContract: Sendable {
    public let initialDestination: WorkbenchDestination
    public let composerPlacement: ComposerPlacement
    public let taskSubmissionBinding: TaskSubmissionBinding
    public let setupAndRecoveryPlacement: SetupAndRecoveryPlacement
    public let modelSelection: ModelSelectionContract
    public let history: TaskHistoryContract
    public let recovery: TaskRecoveryContract

    public static let productDefault = WorkbenchSurfaceContract(
        initialDestination: .newTask,
        composerPlacement: .firstScreen,
        taskSubmissionBinding: .supervisorUnifiedTask,
        setupAndRecoveryPlacement: .separateSettings,
        modelSelection: ModelSelectionContract(
            placement: .composerToolbar,
            defaultChoice: .automaticLocalFirst,
            availableChoices: [.automaticLocalFirst, .localOnly, .cloudWithApproval],
            cloudGuard: .credentialAndPerRequestApproval
        ),
        history: TaskHistoryContract(
            placement: .primaryNavigation,
            source: .persistedTaskRecords,
            emptyState: .explicitNoHistory,
            previewFixturesAllowed: false
        ),
        recovery: TaskRecoveryContract(
            placement: .taskDetail,
            visibleStates: [.blocked, .failed, .interrupted, .unknown],
            resumeSource: .persistedTaskAndVerifiedNativeSession,
            reconciliation: .freshSnapshotAndRevisionBeforeResume,
            forceTermination: .separateExplicitApproval
        )
    )
}

public enum ManifestArgumentResolver {
    public static func explicitManifestPath(in arguments: [String]) -> String? {
        guard let flag = arguments.firstIndex(of: "--manifest") else { return nil }
        let value = arguments.index(after: flag)
        guard value < arguments.endIndex, !arguments[value].hasPrefix("-") else { return nil }
        return arguments[value]
    }
}

public enum ManifestValidationError: Error, Equatable, CustomStringConvertible {
    case unsupportedSchema(Int)
    case wrongComponentSet([String])
    case duplicateStartOrder
    case invalidPort(String, Int)
    case duplicatePort(Int)
    case updateGateBypass(String)
    case selfUpdateEnabled(String)
    case unverifiedHealthPromoted(String)
    case invalidSecretsLocation(String)
    case holaOSDistributionBoundaryLost(String)

    public var description: String {
        switch self {
        case .unsupportedSchema(let version): "unsupported schema version: \(version)"
        case .wrongComponentSet(let ids): "unexpected component set: \(ids.sorted())"
        case .duplicateStartOrder: "component start order must be unique"
        case .invalidPort(let id, let port): "invalid port \(port) for \(id)"
        case .duplicatePort(let port): "duplicate component port: \(port)"
        case .updateGateBypass(let id): "\(id) bypasses the product compatibility gate"
        case .selfUpdateEnabled(let id): "\(id) self-update must remain disabled"
        case .unverifiedHealthPromoted(let id): "\(id) health was promoted without adapter evidence"
        case .invalidSecretsLocation(let value): "secrets must use Keychain, got \(value)"
        case .holaOSDistributionBoundaryLost(let mode): "holaOS install mode is not license-safe: \(mode)"
        }
    }
}

public struct ProductManifest: Codable, Sendable {
    public let schemaVersion: Int
    public let productID: String
    public let manifestVersion: String
    public let paths: [String: String]
    public let components: [Component]
    public let productServices: [ProductService]
    public let lifecycle: LifecycleSteps

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case productID = "product_id"
        case manifestVersion = "manifest_version"
        case paths, components, lifecycle
        case productServices = "product_services"
    }

    public init(data: Data) throws {
        self = try JSONDecoder().decode(Self.self, from: data)
        try validate()
    }

    public static func load(from url: URL) throws -> Self {
        try Self(data: Data(contentsOf: url))
    }

    public func validate() throws {
        guard schemaVersion == 1 else {
            throw ManifestValidationError.unsupportedSchema(schemaVersion)
        }
        let expected = Set(["semantica", "holaos", "herdr", "omlx"])
        let ids = components.map(\.id)
        guard Set(ids) == expected, ids.count == expected.count else {
            throw ManifestValidationError.wrongComponentSet(ids)
        }
        guard Set(components.map(\.startOrder)).count == components.count else {
            throw ManifestValidationError.duplicateStartOrder
        }

        var ports = Set<Int>()
        for component in components {
            if let port = component.port {
                guard (1024...65535).contains(port) else {
                    throw ManifestValidationError.invalidPort(component.id, port)
                }
                guard ports.insert(port).inserted else {
                    throw ManifestValidationError.duplicatePort(port)
                }
            }
            guard component.updateOwner == "product_compatibility_gate" else {
                throw ManifestValidationError.updateGateBypass(component.id)
            }
            guard component.allowSelfUpdate == false else {
                throw ManifestValidationError.selfUpdateEnabled(component.id)
            }
            guard component.healthContract == "pending-adapter-verification" else {
                throw ManifestValidationError.unverifiedHealthPromoted(component.id)
            }
        }
        guard productServices.map(\.id) == ["inference-broker", "governed-memory-service"] else {
            throw ManifestValidationError.wrongComponentSet(productServices.map(\.id))
        }
        for service in productServices {
            guard (1024...65535).contains(service.port) else {
                throw ManifestValidationError.invalidPort(service.id, service.port)
            }
            guard ports.insert(service.port).inserted else {
                throw ManifestValidationError.duplicatePort(service.port)
            }
        }
        guard let secrets = paths["secrets"], secrets.hasPrefix("keychain://") else {
            throw ManifestValidationError.invalidSecretsLocation(paths["secrets"] ?? "missing")
        }
        guard let holaOS = components.first(where: { $0.id == "holaos" }),
              holaOS.installMode == "external_user_install_pending_license_clearance" else {
            throw ManifestValidationError.holaOSDistributionBoundaryLost(
                components.first(where: { $0.id == "holaos" })?.installMode ?? "missing"
            )
        }
    }

    public var startPlan: [Component] {
        components.sorted { $0.startOrder < $1.startOrder }
    }

    public var stopPlan: [Component] {
        startPlan.reversed()
    }
}

public struct ProductService: Codable, Sendable, Identifiable {
    public let id: String
    public let port: Int
}

public struct Component: Codable, Sendable, Identifiable {
    public let id: String
    public let version: String
    public let installMode: String
    public let runtime: String
    public let startOrder: Int
    public let port: Int?
    public let healthContract: String
    public let updateOwner: String
    public let allowSelfUpdate: Bool
    public let dataPath: String

    enum CodingKeys: String, CodingKey {
        case id, version, runtime, port
        case installMode = "install_mode"
        case startOrder = "start_order"
        case healthContract = "health_contract"
        case updateOwner = "update_owner"
        case allowSelfUpdate = "allow_self_update"
        case dataPath = "data_path"
    }
}

public struct LifecycleSteps: Codable, Sendable {
    public let installSteps: [String]
    public let uninstallSteps: [String]

    enum CodingKeys: String, CodingKey {
        case installSteps = "install_steps"
        case uninstallSteps = "uninstall_steps"
    }
}

public struct LauncherSummary: Codable, Sendable {
    public let productID: String
    public let manifestVersion: String
    public let status: String
    public let startPlan: [String]
    public let stopPlan: [String]
    public let ports: [String: Int]

    public init(manifest: ProductManifest) {
        productID = manifest.productID
        manifestVersion = manifest.manifestVersion
        status = "contract-valid"
        startPlan = manifest.startPlan.map(\.id)
        stopPlan = manifest.stopPlan.map(\.id)
        let componentPorts = manifest.components.compactMap { component in
            component.port.map { (component.id, $0) }
        }
        let servicePorts = manifest.productServices.map { ($0.id, $0.port) }
        ports = Dictionary(uniqueKeysWithValues: componentPorts + servicePorts)
    }
}
