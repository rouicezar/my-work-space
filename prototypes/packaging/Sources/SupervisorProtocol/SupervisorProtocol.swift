import Foundation

public enum SupervisorProtocolError: Error, Equatable, CustomStringConvertible {
    case executableMustBeAbsolute
    case requestTooLarge
    case outputTooLarge
    case invalidResponse(String)
    case commandMismatch
    case requestMismatch
    case supervisorFailed(String, String)

    public var description: String {
        switch self {
        case .executableMustBeAbsolute: "Supervisor executable must be an absolute file URL"
        case .requestTooLarge: "Supervisor request exceeded the configured limit"
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
    public let capabilities: [String]
    public let quantizationBits: Int?
    public let embeddingDimension: Int?
    public let queryPrefix: String?
    public let documentPrefix: String?
    public let sizeBytes: Int64
    public let sourcePath: String
    public let availableVerified: Bool
    public let unavailableReason: String?
    public let approvalRequired: Bool

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case modelID = "model_id"
        case repository, revision, license, capabilities
        case quantizationBits = "quantization_bits"
        case embeddingDimension = "embedding_dimension"
        case queryPrefix = "query_prefix"
        case documentPrefix = "document_prefix"
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

public struct EmbeddingActivationPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let route: EmbeddingRoutePayload
    public let reference: ModelReferencePayload

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case route, reference
    }
}

public struct ModelDownloadPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let modelID: String
    public let revision: String
    public let snapshotPath: String
    public let totalSizeBytes: Int64
    public let transferredBytes: Int64
    public let reusedFiles: Int
    public let downloadedFiles: Int

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case modelID = "model_id"
        case revision
        case snapshotPath = "snapshot_path"
        case totalSizeBytes = "total_size_bytes"
        case transferredBytes = "transferred_bytes"
        case reusedFiles = "reused_files"
        case downloadedFiles = "downloaded_files"
    }
}

public struct EmbeddingRoutePayload: Decodable, Sendable {
    public let modelID: String
    public let apiModel: String
    public let revision: String
    public let expectedDimension: Int

    enum CodingKeys: String, CodingKey {
        case modelID = "model_id"
        case apiModel = "api_model"
        case revision
        case expectedDimension = "expected_dimension"
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

public struct RuntimeStatusPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let phase: String
    public let record: RuntimeRecordPayload?
    public let omlxAlive: Bool
    public let brokerAlive: Bool
    public let memoryAlive: Bool?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case phase, record
        case omlxAlive = "omlx_alive"
        case brokerAlive = "broker_alive"
        case memoryAlive = "memory_alive"
    }
}

public struct RuntimeCommandPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let runtime: RuntimeRecordPayload

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case runtime
    }
}

public struct RuntimeRecordPayload: Decodable, Sendable {
    public let phase: String
    public let correlationID: String
    public let revision: Int

    enum CodingKeys: String, CodingKey {
        case phase, revision
        case correlationID = "correlation_id"
    }
}

public struct SampleTaskPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let correlationID: String
    public let model: String
    public let output: String
    public let auditPath: String

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case correlationID = "correlation_id"
        case model, output
        case auditPath = "audit_path"
    }
}

public struct LocalTaskPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let route: String
    public let correlationID: String
    public let model: String
    public let output: String
    public let finishReason: String
    public let promptTokens: Int?
    public let completionTokens: Int?
    public let totalTokens: Int?
    public let auditPath: String

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case route
        case correlationID = "correlation_id"
        case model, output
        case finishReason = "finish_reason"
        case promptTokens = "prompt_tokens"
        case completionTokens = "completion_tokens"
        case totalTokens = "total_tokens"
        case auditPath = "audit_path"
    }
}

private struct LocalTaskInput: Encodable {
    let schemaVersion = 1
    let prompt: String
    let maximumOutputTokens: Int

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case prompt
        case maximumOutputTokens = "maximum_output_tokens"
    }
}

public struct CloudCostEstimatePayload: Decodable, Sendable {
    public let currency: String
    public let minimum: Double
    public let maximum: Double
    public let pricingSource: String
    public let pricingEffectiveAt: String

    enum CodingKeys: String, CodingKey {
        case currency, minimum, maximum
        case pricingSource = "pricing_source"
        case pricingEffectiveAt = "pricing_effective_at"
    }
}

public struct CloudProposalPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let proposalID: String
    public let correlationID: String
    public let providerID: String
    public let modelID: String
    public let reasonCodes: [String]
    public let payloadSHA256: String
    public let payloadSizeBytes: Int
    public let dataClasses: [String]
    public let redactions: [String]
    public let maximumOutputTokens: Int
    public let estimatedCost: CloudCostEstimatePayload
    public let processingLocation: String
    public let retention: String
    public let trainingOptOutState: String
    public let privacyPolicyURL: String

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case proposalID = "proposal_id"
        case correlationID = "correlation_id"
        case providerID = "provider_id"
        case modelID = "model_id"
        case reasonCodes = "reason_codes"
        case payloadSHA256 = "payload_sha256"
        case payloadSizeBytes = "payload_size_bytes"
        case dataClasses = "data_classes"
        case redactions
        case maximumOutputTokens = "maximum_output_tokens"
        case estimatedCost = "estimated_cost"
        case processingLocation = "processing_location"
        case retention
        case trainingOptOutState = "training_opt_out_state"
        case privacyPolicyURL = "privacy_policy_url"
    }
}

public struct CloudPreviewPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let proposal: CloudProposalPayload
    public let approvalRequired: Bool

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case proposal
        case approvalRequired = "approval_required"
    }
}

public struct CloudApprovalRecordPayload: Decodable, Sendable {
    public let proposalID: String
    public let maximumCostUSD: Double
    public let approvedAt: String
    public let expiresAt: String
    public let consumedAt: String?

    enum CodingKeys: String, CodingKey {
        case proposalID = "proposal_id"
        case maximumCostUSD = "maximum_cost_usd"
        case approvedAt = "approved_at"
        case expiresAt = "expires_at"
        case consumedAt = "consumed_at"
    }
}

public struct CloudApprovalPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let approval: CloudApprovalRecordPayload

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case approval
    }
}

public struct CloudDecisionPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let proposalID: String
    public let outcome: String

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case proposalID = "proposal_id"
        case outcome
    }
}

public struct CloudUsagePayload: Decodable, Sendable {
    public let promptTokens: Int
    public let promptCacheHitTokens: Int
    public let promptCacheMissTokens: Int
    public let completionTokens: Int
    public let totalTokens: Int
    public let costUSD: Double

    enum CodingKeys: String, CodingKey {
        case promptTokens = "prompt_tokens"
        case promptCacheHitTokens = "prompt_cache_hit_tokens"
        case promptCacheMissTokens = "prompt_cache_miss_tokens"
        case completionTokens = "completion_tokens"
        case totalTokens = "total_tokens"
        case costUSD = "cost_usd"
    }
}

public indirect enum JSONValue: Decodable, Sendable {
    case string(String)
    case number(Double)
    case boolean(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    public init(from decoder: Decoder) throws {
        let value = try decoder.singleValueContainer()
        if value.decodeNil() { self = .null }
        else if let item = try? value.decode(Bool.self) { self = .boolean(item) }
        else if let item = try? value.decode(Double.self) { self = .number(item) }
        else if let item = try? value.decode(String.self) { self = .string(item) }
        else if let item = try? value.decode([String: JSONValue].self) { self = .object(item) }
        else if let item = try? value.decode([JSONValue].self) { self = .array(item) }
        else { throw DecodingError.dataCorruptedError(in: value, debugDescription: "unsupported JSON value") }
    }
}

public struct CloudResultPayload: Decodable, Sendable {
    public let model: String
    public let content: String
    public let finishReason: String
    public let toolProposals: [JSONValue]
    public let usage: CloudUsagePayload

    enum CodingKeys: String, CodingKey {
        case model, content, usage
        case finishReason = "finish_reason"
        case toolProposals = "tool_proposals"
    }
}

public struct CloudExecutionPayload: Decodable, Sendable {
    public let schemaVersion: Int
    public let result: CloudResultPayload

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case result
    }
}

public struct SupervisorClient: Sendable {
    public let executableURL: URL
    public let maximumResponseBytes: Int
    public let maximumRequestBytes: Int

    public init(
        executableURL: URL,
        maximumResponseBytes: Int = 1_048_576,
        maximumRequestBytes: Int = 8_388_608
    ) throws {
        guard executableURL.isFileURL, executableURL.path.hasPrefix("/") else {
            throw SupervisorProtocolError.executableMustBeAbsolute
        }
        self.executableURL = executableURL
        self.maximumResponseBytes = maximumResponseBytes
        self.maximumRequestBytes = maximumRequestBytes
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

    public func embeddingPlan(
        rootURL: URL,
        cacheRootURL: URL,
        catalogURL: URL,
        requestID: UUID = UUID()
    ) throws -> ModelPlanPayload {
        try request(
            command: "embedding-plan",
            arguments: ["--root", rootURL.path, "--cache-root", cacheRootURL.path,
                        "--catalog", catalogURL.path],
            requestID: requestID
        )
    }

    public func activateEmbedding(
        rootURL: URL,
        cacheRootURL: URL,
        catalogURL: URL,
        approvedRevision: String,
        requestID: UUID = UUID()
    ) throws -> EmbeddingActivationPayload {
        try request(
            command: "activate-embedding",
            arguments: ["--root", rootURL.path, "--cache-root", cacheRootURL.path,
                        "--catalog", catalogURL.path, "--approve-revision", approvedRevision],
            requestID: requestID
        )
    }

    public func downloadEmbedding(
        rootURL: URL,
        cacheRootURL: URL,
        catalogURL: URL,
        approvedRevision: String,
        requestID: UUID = UUID()
    ) throws -> ModelDownloadPayload {
        try request(
            command: "download-embedding",
            arguments: ["--root", rootURL.path, "--cache-root", cacheRootURL.path,
                        "--catalog", catalogURL.path, "--approve-revision", approvedRevision],
            requestID: requestID
        )
    }

    public func runtimeStatus(rootURL: URL, requestID: UUID = UUID()) throws -> RuntimeStatusPayload {
        try request(
            command: "runtime-status", arguments: ["--root", rootURL.path], requestID: requestID
        )
    }

    public func startRuntime(
        rootURL: URL,
        omlxAPIKey: String,
        brokerToken: String,
        memoryToken: String,
        requestID: UUID = UUID()
    ) throws -> RuntimeCommandPayload {
        try request(
            command: "start-runtime",
            arguments: ["--root", rootURL.path],
            requestID: requestID,
            environmentOverrides: [
                "OMLX_API_KEY": omlxAPIKey,
                "MAC_AI_WORK_OS_BROKER_TOKEN": brokerToken,
                "MAC_AI_WORK_OS_MEMORY_TOKEN": memoryToken,
            ]
        )
    }

    public func stopRuntime(rootURL: URL, requestID: UUID = UUID()) throws -> RuntimeCommandPayload {
        try request(
            command: "stop-runtime", arguments: ["--root", rootURL.path], requestID: requestID
        )
    }

    public func sampleTask(
        rootURL: URL,
        omlxAPIKey: String,
        brokerToken: String,
        memoryToken: String,
        requestID: UUID = UUID()
    ) throws -> SampleTaskPayload {
        try request(
            command: "sample-task",
            arguments: ["--root", rootURL.path],
            requestID: requestID,
            environmentOverrides: [
                "OMLX_API_KEY": omlxAPIKey,
                "MAC_AI_WORK_OS_BROKER_TOKEN": brokerToken,
                "MAC_AI_WORK_OS_MEMORY_TOKEN": memoryToken,
            ]
        )
    }

    public func localTask(
        rootURL: URL,
        prompt: String,
        maximumOutputTokens: Int,
        omlxAPIKey: String,
        brokerToken: String,
        memoryToken: String,
        requestID: UUID = UUID()
    ) throws -> LocalTaskPayload {
        guard prompt.lengthOfBytes(using: .utf8) <= 262_144 else {
            throw SupervisorProtocolError.requestTooLarge
        }
        let input: Data
        do {
            input = try JSONEncoder().encode(LocalTaskInput(
                prompt: prompt, maximumOutputTokens: maximumOutputTokens
            ))
        } catch {
            throw SupervisorProtocolError.invalidResponse("could not encode local task")
        }
        return try request(
            command: "local-task",
            arguments: ["--root", rootURL.path],
            requestID: requestID,
            environmentOverrides: [
                "OMLX_API_KEY": omlxAPIKey,
                "MAC_AI_WORK_OS_BROKER_TOKEN": brokerToken,
                "MAC_AI_WORK_OS_MEMORY_TOKEN": memoryToken,
            ],
            inputData: input
        )
    }

    public func cloudPreview(
        rootURL: URL,
        catalogURL: URL,
        modelID: String,
        estimatedInputTokens: Int,
        maximumOutputTokens: Int,
        minimumAvailableMemoryMB: Int,
        requiredCapabilities: [String],
        dataClasses: [String],
        reasonCodes: [String],
        redactions: [String],
        outboundBody: Data,
        requestID: UUID = UUID()
    ) throws -> CloudPreviewPayload {
        var arguments = [
            "--root", rootURL.path, "--catalog", catalogURL.path,
            "--model-id", modelID,
            "--estimated-input-tokens", String(estimatedInputTokens),
            "--maximum-output-tokens", String(maximumOutputTokens),
            "--minimum-available-memory-mb", String(minimumAvailableMemoryMB),
        ]
        for value in requiredCapabilities { arguments += ["--required-capability", value] }
        for value in dataClasses { arguments += ["--data-class", value] }
        for value in reasonCodes { arguments += ["--reason-code", value] }
        for value in redactions { arguments += ["--redaction", value] }
        return try request(
            command: "cloud-preview", arguments: arguments, requestID: requestID,
            inputData: outboundBody
        )
    }

    public func approveCloud(
        rootURL: URL,
        proposalID: String,
        maximumCostUSD: Double,
        requestID: UUID = UUID()
    ) throws -> CloudApprovalPayload {
        try request(
            command: "cloud-approve",
            arguments: ["--root", rootURL.path, "--proposal-id", proposalID,
                        "--maximum-cost-usd", String(maximumCostUSD)],
            requestID: requestID
        )
    }

    public func rejectCloud(
        rootURL: URL,
        proposalID: String,
        requestID: UUID = UUID()
    ) throws -> CloudDecisionPayload {
        try request(
            command: "cloud-reject",
            arguments: ["--root", rootURL.path, "--proposal-id", proposalID],
            requestID: requestID
        )
    }

    public func executeCloud(
        rootURL: URL,
        catalogURL: URL,
        proposalID: String,
        deepSeekAPIKey: String,
        requestID: UUID = UUID()
    ) throws -> CloudExecutionPayload {
        try request(
            command: "cloud-execute",
            arguments: ["--root", rootURL.path, "--catalog", catalogURL.path,
                        "--proposal-id", proposalID],
            requestID: requestID,
            environmentOverrides: ["MAC_AI_WORK_OS_DEEPSEEK_API_KEY": deepSeekAPIKey]
        )
    }

    private func request<Payload: Decodable & Sendable>(
        command: String,
        arguments: [String],
        requestID: UUID,
        environmentOverrides: [String: String] = [:],
        inputData: Data? = nil
    ) throws -> Payload {
        let request = requestID.uuidString.lowercased()
        let invocation = try invoke(
            arguments: ["--request-id", request, command] + arguments,
            environmentOverrides: environmentOverrides,
            inputData: inputData
        )
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

    private func invoke(
        arguments: [String],
        environmentOverrides: [String: String] = [:],
        inputData: Data? = nil
    ) throws -> (data: Data, exitStatus: Int32) {
        if let inputData, inputData.count > maximumRequestBytes {
            throw SupervisorProtocolError.requestTooLarge
        }
        let process = Process()
        let output = Pipe()
        let input = inputData == nil ? nil : Pipe()
        process.executableURL = executableURL
        process.arguments = arguments
        if !environmentOverrides.isEmpty {
            var environment = ProcessInfo.processInfo.environment
            for (name, value) in environmentOverrides { environment[name] = value }
            process.environment = environment
        }
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        if let input { process.standardInput = input }
        do {
            try process.run()
        } catch {
            throw SupervisorProtocolError.invalidResponse("could not launch Supervisor")
        }
        if let inputData, let input {
            input.fileHandleForWriting.write(inputData)
            try input.fileHandleForWriting.close()
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
