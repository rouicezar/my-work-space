import Foundation

public enum SupervisorProtocolError: Error, Equatable, CustomStringConvertible {
    case executableMustBeAbsolute
    case outputTooLarge
    case invalidResponse(String)
    case commandMismatch
    case requestMismatch
    case supervisorFailed(String, String)

    public var description: String {
        switch self {
        case .executableMustBeAbsolute: "Supervisor executable must be an absolute file URL"
        case .outputTooLarge: "Supervisor response exceeded the configured limit"
        case .invalidResponse(let detail): "Invalid Supervisor response: \(detail)"
        case .commandMismatch: "Supervisor response command did not match the request"
        case .requestMismatch: "Supervisor response request ID did not match the request"
        case .supervisorFailed(let code, let message): "Supervisor failed (\(code)): \(message)"
        }
    }
}

public struct SupervisorEnvelope<Payload: Decodable & Sendable>: Decodable, Sendable {
    public let schemaVersion: Int
    public let command: String
    public let requestID: String
    public let status: String
    public let payload: Payload?
    public let error: SupervisorRemoteError?
    public let emittedAt: String

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case command
        case requestID = "request_id"
        case status, payload, error
        case emittedAt = "emitted_at"
    }
}

public struct SupervisorRemoteError: Decodable, Sendable {
    public let code: String
    public let message: String
}

public struct PreflightPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let status: String
    public let selectedProfile: PreflightProfile?
    public let blockers: [PreflightFinding]
    public let unknowns: [PreflightFinding]
    public let notice: String

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case status
        case selectedProfile = "selected_profile"
        case blockers, unknowns, notice
    }
}

public struct PreflightProfile: Decodable, Sendable {
    public let id: String
    public let label: String
    public let status: String
}

public struct PreflightFinding: Decodable, Sendable, Identifiable {
    public let code: String
    public let message: String
    public var id: String { "\(code):\(message)" }
}

public struct InstallationPlanPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let component: String
    public let release: String
    public let artifactName: String
    public let artifactSizeBytes: Int64
    public let artifactSHA256: String
    public let downloadedBytes: Int64
    public let cachedArtifactVerified: Bool
    public let cacheBlocker: String?
    public let productRoot: String
    public let alreadyActive: Bool
    public let approvalRequired: Bool

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case component, release
        case artifactName = "artifact_name"
        case artifactSizeBytes = "artifact_size_bytes"
        case artifactSHA256 = "artifact_sha256"
        case downloadedBytes = "downloaded_bytes"
        case cachedArtifactVerified = "cached_artifact_verified"
        case cacheBlocker = "cache_blocker"
        case productRoot = "product_root"
        case alreadyActive = "already_active"
        case approvalRequired = "approval_required"
    }
}

public struct InstallationStatusPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let component: String
    public let operation: InstallationOperation?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case component, operation
    }
}

public struct InstallationOperation: Decodable, Sendable {
    public let operationID: String
    public let phase: String
    public let completedSteps: [String]
    public let activeStep: String?
    public let error: [String: String]?

    enum CodingKeys: String, CodingKey {
        case operationID = "operation_id"
        case phase
        case completedSteps = "completed_steps"
        case activeStep = "active_step"
        case error
    }
}

public struct InstalledBundlePayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let active: InstalledBundle

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case active
    }
}

public struct InstalledBundle: Decodable, Sendable {
    public let release: String
    public let appPath: String
    public let shortVersion: String

    enum CodingKeys: String, CodingKey {
        case release
        case appPath = "app_path"
        case shortVersion = "short_version"
    }
}

public struct ModelPlanPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let modelID: String
    public let repository: String
    public let revision: String
    public let license: String
    public let quantizationBits: Int
    public let sizeBytes: Int64
    public let sourcePath: String
    public let availableVerified: Bool
    public let unavailableReason: String?
    public let approvalRequired: Bool

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case modelID = "model_id"
        case repository, revision, license
        case quantizationBits = "quantization_bits"
        case sizeBytes = "size_bytes"
        case sourcePath = "source_path"
        case availableVerified = "available_verified"
        case unavailableReason = "unavailable_reason"
        case approvalRequired = "approval_required"
    }
}

public struct ModelLinkPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let reference: ModelReferencePayload

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case reference
    }
}

public struct ModelReferencePayload: Decodable, Sendable {
    public let modelID: String
    public let revision: String
    public let linkPath: String
    public let storageMode: String
    public let sourceOwnership: String

    enum CodingKeys: String, CodingKey {
        case modelID = "model_id"
        case revision
        case linkPath = "link_path"
        case storageMode = "storage_mode"
        case sourceOwnership = "source_ownership"
    }
}

public struct SupervisorClient: Sendable {
    public let executableURL: URL
    public let maximumResponseBytes: Int

    public init(executableURL: URL, maximumResponseBytes: Int = 1_048_576) throws {
        guard executableURL.isFileURL, executableURL.path.hasPrefix("/") else {
            throw SupervisorProtocolError.executableMustBeAbsolute
        }
        self.executableURL = executableURL
        self.maximumResponseBytes = maximumResponseBytes
    }

    public func preflight(
        profilesURL: URL,
        checkPath: URL,
        ports: [Int],
        requestID: UUID = UUID()
    ) throws -> PreflightPayload {
        let request = requestID.uuidString.lowercased()
        var arguments = [
            "--request-id", request,
            "preflight",
            "--profiles", profilesURL.path,
            "--check-path", checkPath.path,
            "--ports",
        ]
        arguments.append(contentsOf: ports.map(String.init))
        let invocation = try invoke(arguments: arguments)
        let envelope: SupervisorEnvelope<PreflightPayload>
        do {
            envelope = try JSONDecoder().decode(
                SupervisorEnvelope<PreflightPayload>.self,
                from: invocation.data
            )
        } catch {
            throw SupervisorProtocolError.invalidResponse(String(describing: error))
        }
        guard envelope.schemaVersion == 1 else {
            throw SupervisorProtocolError.invalidResponse("unsupported schema")
        }
        guard envelope.command == "preflight" else {
            throw SupervisorProtocolError.commandMismatch
        }
        guard envelope.requestID == request else {
            throw SupervisorProtocolError.requestMismatch
        }
        if envelope.status == "error", let remote = envelope.error {
            throw SupervisorProtocolError.supervisorFailed(remote.code, remote.message)
        }
        guard invocation.exitStatus == 0 else {
            throw SupervisorProtocolError.invalidResponse("successful payload used nonzero exit status")
        }
        guard envelope.status == "ok", let payload = envelope.payload else {
            throw SupervisorProtocolError.invalidResponse("missing successful payload")
        }
        guard payload.schemaVersion == 1 else {
            throw SupervisorProtocolError.invalidResponse("unsupported payload schema")
        }
        guard ["supported", "unknown", "unsupported"].contains(payload.status) else {
            throw SupervisorProtocolError.invalidResponse("unknown preflight status")
        }
        return payload
    }

    public func installationPlan(
        rootURL: URL,
        osMajor: Int,
        upstreamsURL: URL,
        requestID: UUID = UUID()
    ) throws -> InstallationPlanPayload {
        try request(
            command: "installation-plan",
            arguments: ["--root", rootURL.path, "--os-major", String(osMajor),
                        "--upstreams", upstreamsURL.path],
            requestID: requestID
        )
    }

    public func installationStatus(
        rootURL: URL,
        requestID: UUID = UUID()
    ) throws -> InstallationStatusPayload {
        try request(
            command: "installation-status",
            arguments: ["--root", rootURL.path],
            requestID: requestID
        )
    }

    public func installOMLX(
        rootURL: URL,
        osMajor: Int,
        upstreamsURL: URL,
        approvedArtifactSHA256: String,
        requestID: UUID = UUID()
    ) throws -> InstalledBundlePayload {
        try request(
            command: "install-omlx",
            arguments: ["--root", rootURL.path, "--os-major", String(osMajor),
                        "--upstreams", upstreamsURL.path,
                        "--approve-artifact-sha256", approvedArtifactSHA256],
            requestID: requestID
        )
    }

    public func modelPlan(
        rootURL: URL,
        cacheRootURL: URL,
        catalogURL: URL,
        requestID: UUID = UUID()
    ) throws -> ModelPlanPayload {
        try request(
            command: "model-plan",
            arguments: ["--root", rootURL.path, "--cache-root", cacheRootURL.path,
                        "--catalog", catalogURL.path],
            requestID: requestID
        )
    }

    public func linkModel(
        rootURL: URL,
        cacheRootURL: URL,
        catalogURL: URL,
        approvedRevision: String,
        requestID: UUID = UUID()
    ) throws -> ModelLinkPayload {
        try request(
            command: "link-model",
            arguments: ["--root", rootURL.path, "--cache-root", cacheRootURL.path,
                        "--catalog", catalogURL.path, "--approve-revision", approvedRevision],
            requestID: requestID
        )
    }

    private func request<Payload: Decodable & Sendable>(
        command: String,
        arguments: [String],
        requestID: UUID
    ) throws -> Payload {
        let request = requestID.uuidString.lowercased()
        let invocation = try invoke(arguments: ["--request-id", request, command] + arguments)
        let envelope: SupervisorEnvelope<Payload>
        do {
            envelope = try JSONDecoder().decode(SupervisorEnvelope<Payload>.self, from: invocation.data)
        } catch {
            throw SupervisorProtocolError.invalidResponse(String(describing: error))
        }
        guard envelope.schemaVersion == 1 else {
            throw SupervisorProtocolError.invalidResponse("unsupported schema")
        }
        guard envelope.command == command else { throw SupervisorProtocolError.commandMismatch }
        guard envelope.requestID == request else { throw SupervisorProtocolError.requestMismatch }
        if envelope.status == "error", let remote = envelope.error {
            throw SupervisorProtocolError.supervisorFailed(remote.code, remote.message)
        }
        guard invocation.exitStatus == 0 else {
            throw SupervisorProtocolError.invalidResponse("successful payload used nonzero exit status")
        }
        guard envelope.status == "ok", let payload = envelope.payload else {
            throw SupervisorProtocolError.invalidResponse("missing successful payload")
        }
        return payload
    }

    private func invoke(arguments: [String]) throws -> (data: Data, exitStatus: Int32) {
        let process = Process()
        let output = Pipe()
        process.executableURL = executableURL
        process.arguments = arguments
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        do {
            try process.run()
        } catch {
            throw SupervisorProtocolError.invalidResponse("could not launch Supervisor")
        }
        var response = Data()
        while let chunk = try output.fileHandleForReading.read(upToCount: 65_536), !chunk.isEmpty {
            if response.count + chunk.count > maximumResponseBytes {
                process.terminate()
                process.waitUntilExit()
                throw SupervisorProtocolError.outputTooLarge
            }
            response.append(chunk)
        }
        process.waitUntilExit()
        return (response, process.terminationStatus)
    }
}
