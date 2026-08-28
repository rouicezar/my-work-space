import Foundation

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
    public let lifecycle: LifecycleSteps

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case productID = "product_id"
        case manifestVersion = "manifest_version"
        case paths, components, lifecycle
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
        ports = Dictionary(
            uniqueKeysWithValues: manifest.components.compactMap { component in
                component.port.map { (component.id, $0) }
            }
        )
    }
}
