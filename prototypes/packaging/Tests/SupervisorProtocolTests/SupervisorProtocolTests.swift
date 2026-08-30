import Foundation
import Testing
import RuntimeSecurity
@testable import SupervisorProtocol

@Test func decodesAndCorrelatesRealProcessEnvelope() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"preflight","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"status":"supported","selected_profile":{"id":"apple-silicon-16gb","label":"Apple Silicon 16 GB","status":"provisional"},"blockers":[],"unknowns":[],"notice":"provisional"},"error":null,"emitted_at":"2026-08-29T00:00:00+00:00"}"#
    try "#!/bin/sh\nprintf '%s' '\(response)'\n".write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let client = try SupervisorClient(executableURL: executable)
    let requestID = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    let payload = try client.preflight(
        profilesURL: temporary.appendingPathComponent("profiles.json"),
        checkPath: temporary,
        ports: [8000],
        requestID: requestID
    )
    #expect(payload.status == "supported")
    #expect(payload.selectedProfile?.id == "apple-silicon-16gb")
}

@Test func rejectsMismatchedRequestID() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"preflight","request_id":"00000000-0000-0000-0000-000000000002","status":"ok","payload":{"schema_version":1,"status":"supported","selected_profile":null,"blockers":[],"unknowns":[],"notice":"provisional"},"error":null,"emitted_at":"2026-08-29T00:00:00+00:00"}"#
    try "#!/bin/sh\nprintf '%s' '\(response)'\n".write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let client = try SupervisorClient(executableURL: executable)
    #expect(throws: SupervisorProtocolError.requestMismatch) {
        try client.preflight(
            profilesURL: temporary.appendingPathComponent("profiles.json"),
            checkPath: temporary,
            ports: [],
            requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        )
    }
}

@Test func rejectsUnknownPreflightStatus() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"preflight","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"status":"maybe","selected_profile":null,"blockers":[],"unknowns":[],"notice":"provisional"},"error":null,"emitted_at":"2026-08-29T00:00:00+00:00"}"#
    try "#!/bin/sh\nprintf '%s' '\(response)'\n".write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let client = try SupervisorClient(executableURL: executable)
    #expect(throws: SupervisorProtocolError.invalidResponse("unknown preflight status")) {
        try client.preflight(
            profilesURL: temporary.appendingPathComponent("profiles.json"),
            checkPath: temporary,
            ports: [],
            requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        )
    }
}

@Test func surfacesStructuredSupervisorErrorWithoutRequiringPayload() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"preflight","request_id":"00000000-0000-0000-0000-000000000001","status":"error","payload":null,"error":{"code":"PROBE_FAILED","message":"fixture failure"},"emitted_at":"2026-08-29T00:00:00+00:00"}"#
    try "#!/bin/sh\nprintf '%s' '\(response)'\nexit 2\n".write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let client = try SupervisorClient(executableURL: executable)
    #expect(throws: SupervisorProtocolError.supervisorFailed("PROBE_FAILED", "fixture failure")) {
        try client.preflight(
            profilesURL: temporary.appendingPathComponent("profiles.json"),
            checkPath: temporary,
            ports: [],
            requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        )
    }
}

@Test func terminatesAndRejectsOversizeSupervisorOutput() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    try "#!/bin/sh\nprintf 'this response is too large'\n".write(
        to: executable, atomically: true, encoding: .utf8
    )
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let client = try SupervisorClient(executableURL: executable, maximumResponseBytes: 8)
    #expect(throws: SupervisorProtocolError.outputTooLarge) {
        try client.preflight(
            profilesURL: temporary.appendingPathComponent("profiles.json"),
            checkPath: temporary,
            ports: [],
            requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        )
    }
}

@Test func installationPlanBindsExactArtifactAndDestination() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"installation-plan","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"component":"omlx","release":"v0.6.3","artifact_name":"omlx.dmg","artifact_size_bytes":807057789,"artifact_sha256":"abc","downloaded_bytes":42,"cached_artifact_verified":false,"cache_blocker":null,"product_root":"/tmp/Product","already_active":false,"approval_required":true},"error":null,"emitted_at":"2026-08-29T00:00:00+00:00"}"#
    try "#!/bin/sh\nprintf '%s' '\(response)'\n".write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let payload = try SupervisorClient(executableURL: executable).installationPlan(
        rootURL: temporary.appendingPathComponent("Product"), osMajor: 26,
        upstreamsURL: temporary.appendingPathComponent("upstreams.json"),
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    )
    #expect(payload.release == "v0.6.3")
    #expect(payload.artifactSizeBytes == 807057789)
    #expect(payload.approvalRequired)
}

@Test func modelPlanExposesVerifiedZeroCopyCandidate() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"model-plan","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"model_id":"qwen","repository":"test/qwen","revision":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","license":"Apache-2.0","capabilities":["chat"],"quantization_bits":4,"size_bytes":351000000,"source_path":"/tmp/cache/qwen","available_verified":true,"unavailable_reason":null,"approval_required":true},"error":null,"emitted_at":"2026-08-29T00:00:00+00:00"}"#
    try "#!/bin/sh\nprintf '%s' '\(response)'\n".write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let payload = try SupervisorClient(executableURL: executable).modelPlan(
        rootURL: temporary.appendingPathComponent("Product"),
        cacheRootURL: temporary.appendingPathComponent("cache"),
        catalogURL: temporary.appendingPathComponent("models.json"),
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    )
    #expect(payload.availableVerified)
    #expect(payload.quantizationBits == 4)
    #expect(payload.capabilities == ["chat"])
    #expect(payload.approvalRequired)
}

@Test func embeddingPlanAndActivationExposePinnedMemoryContract() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let plan = #"{"schema_version":1,"command":"embedding-plan","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"model_id":"e5","repository":"test/e5","revision":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","license":"MIT","capabilities":["embedding"],"quantization_bits":null,"embedding_dimension":384,"query_prefix":"query: ","document_prefix":"passage: ","size_bytes":252418075,"source_path":"/tmp/cache/e5","available_verified":false,"unavailable_reason":"MODEL_SNAPSHOT_MISSING","approval_required":true},"error":null,"emitted_at":"2026-08-30T00:00:00+00:00"}"#
    let download = #"{"schema_version":1,"command":"download-embedding","request_id":"00000000-0000-0000-0000-000000000003","status":"ok","payload":{"schema_version":1,"model_id":"e5","revision":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","snapshot_path":"/tmp/cache/e5","total_size_bytes":252418075,"transferred_bytes":252418075,"reused_files":0,"downloaded_files":5},"error":null,"emitted_at":"2026-08-30T00:00:00+00:00"}"#
    let activation = #"{"schema_version":1,"command":"activate-embedding","request_id":"00000000-0000-0000-0000-000000000002","status":"ok","payload":{"schema_version":1,"route":{"model_id":"e5","api_model":"e5","revision":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","expected_dimension":384,"query_prefix":"query: ","document_prefix":"passage: "},"reference":{"model_id":"e5","revision":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","link_path":"/tmp/product/models/e5","storage_mode":"external-reference","source_ownership":"external-cache-not-product-owned"}},"error":null,"emitted_at":"2026-08-30T00:00:00+00:00"}"#
    let script = """
    #!/bin/sh
    case " $* " in
      *" embedding-plan "*) printf '%s' '\(plan)' ;;
      *" download-embedding "*) printf '%s' '\(download)' ;;
      *" activate-embedding "*) printf '%s' '\(activation)' ;;
      *) exit 9 ;;
    esac
    """
    try script.write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let client = try SupervisorClient(executableURL: executable)
    let root = temporary.appendingPathComponent("Product")
    let cache = temporary.appendingPathComponent("cache")
    let catalog = temporary.appendingPathComponent("models.json")
    let planned = try client.embeddingPlan(
        rootURL: root, cacheRootURL: cache, catalogURL: catalog,
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    )
    #expect(planned.quantizationBits == nil)
    #expect(planned.embeddingDimension == 384)
    #expect(planned.queryPrefix == "query: ")
    #expect(!planned.availableVerified)
    let downloaded = try client.downloadEmbedding(
        rootURL: root, cacheRootURL: cache, catalogURL: catalog,
        approvedRevision: planned.revision,
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000003")!
    )
    #expect(downloaded.totalSizeBytes == 252418075)
    #expect(downloaded.downloadedFiles == 5)
    let activated = try client.activateEmbedding(
        rootURL: root, cacheRootURL: cache, catalogURL: catalog,
        approvedRevision: planned.revision,
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000002")!
    )
    #expect(activated.route.expectedDimension == 384)
    #expect(activated.reference.storageMode == "external-reference")
}

@Test func runtimeSecretsTravelInEnvironmentNotArguments() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"start-runtime","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"runtime":{"phase":"running","correlation_id":"test","revision":4}},"error":null,"emitted_at":"2026-08-30T00:00:00+00:00"}"#
    let script = """
    #!/bin/sh
    case " $* " in *fixture-omlx-secret*|*fixture-broker-secret*|*fixture-memory-secret*) exit 9;; esac
    [ "$OMLX_API_KEY" = "fixture-omlx-secret-with-at-least-32-characters" ] || exit 8
    [ "$MAC_AI_WORK_OS_BROKER_TOKEN" = "fixture-broker-secret-with-at-least-32-characters" ] || exit 7
    [ "$MAC_AI_WORK_OS_MEMORY_TOKEN" = "fixture-memory-secret-with-at-least-32-characters" ] || exit 6
    printf '%s' '\(response)'
    """
    try script.write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let payload = try SupervisorClient(executableURL: executable).startRuntime(
        rootURL: temporary.appendingPathComponent("Product"),
        omlxAPIKey: "fixture-omlx-secret-with-at-least-32-characters",
        brokerToken: "fixture-broker-secret-with-at-least-32-characters",
        memoryToken: "fixture-memory-secret-with-at-least-32-characters",
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    )
    #expect(payload.runtime.phase == "running")
}

@Test func cloudPreviewBodyUsesStandardInputAndExecutionKeyUsesEnvironment() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let preview = #"{"schema_version":1,"command":"cloud-preview","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"proposal":{"schema_version":1,"proposal_id":"00000000-0000-0000-0000-000000000010","correlation_id":"00000000-0000-0000-0000-000000000001","provider_id":"deepseek","model_id":"deepseek-v4-flash","reason_codes":["local_validation_failed"],"payload_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","payload_size_bytes":120,"data_classes":["user_text"],"redactions":[],"maximum_output_tokens":1000,"estimated_cost":{"currency":"USD","minimum":0.001,"maximum":0.002,"pricing_source":"https://example.test/pricing","pricing_effective_at":"2026-08-30T00:00:00Z"},"processing_location":"PRC","retention":"variable","training_opt_out_state":"unknown","privacy_policy_url":"https://example.test/privacy"},"approval_required":true},"error":null,"emitted_at":"2026-08-30T00:00:00+00:00"}"#
    let execution = #"{"schema_version":1,"command":"cloud-execute","request_id":"00000000-0000-0000-0000-000000000002","status":"ok","payload":{"schema_version":1,"result":{"model":"deepseek-v4-flash","content":"cloud result","finish_reason":"stop","tool_proposals":[{"id":"call-1","function":{"name":"draft_only"}}],"usage":{"prompt_tokens":10,"prompt_cache_hit_tokens":0,"prompt_cache_miss_tokens":10,"completion_tokens":2,"total_tokens":12,"cost_usd":0.00001}}},"error":null,"emitted_at":"2026-08-30T00:00:00+00:00"}"#
    let script = """
    #!/bin/sh
    case " $* " in
      *" cloud-preview "*)
        case " $* " in *private-fixture-text*) exit 9;; esac
        body=$(cat)
        case "$body" in *private-fixture-text*) ;; *) exit 8;; esac
        printf '%s' '\(preview)'
        ;;
      *" cloud-execute "*)
        case " $* " in *deepseek-secret*) exit 7;; esac
        [ "$MAC_AI_WORK_OS_DEEPSEEK_API_KEY" = "deepseek-secret" ] || exit 6
        printf '%s' '\(execution)'
        ;;
      *) exit 5 ;;
    esac
    """
    try script.write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let client = try SupervisorClient(executableURL: executable)
    let root = temporary.appendingPathComponent("Product")
    let catalog = temporary.appendingPathComponent("cloud-providers.json")
    let requestOne = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    let body = Data(#"{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"private-fixture-text"}],"max_tokens":1000,"stream":false}"#.utf8)
    let proposal = try client.cloudPreview(
        rootURL: root, catalogURL: catalog, modelID: "deepseek-v4-flash",
        estimatedInputTokens: 100, maximumOutputTokens: 1000,
        minimumAvailableMemoryMB: 1024, requiredCapabilities: ["chat"],
        dataClasses: ["user_text"], reasonCodes: ["local_validation_failed"],
        redactions: [], outboundBody: body, requestID: requestOne
    )
    #expect(proposal.approvalRequired)
    #expect(proposal.proposal.estimatedCost.maximum == 0.002)
    let result = try client.executeCloud(
        rootURL: root, catalogURL: catalog, proposalID: proposal.proposal.proposalID,
        deepSeekAPIKey: "deepseek-secret",
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000002")!
    )
    #expect(result.result.content == "cloud result")
    #expect(result.result.toolProposals.count == 1)
}

@Test func localTaskPromptUsesStandardInputAndRuntimeSecretsUseEnvironment() throws {
    let temporary = FileManager.default.temporaryDirectory
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: temporary) }
    let executable = temporary.appendingPathComponent("fixture-supervisor")
    let response = #"{"schema_version":1,"command":"local-task","request_id":"00000000-0000-0000-0000-000000000001","status":"ok","payload":{"schema_version":1,"route":"local","correlation_id":"00000000-0000-0000-0000-000000000001","model":"qwen","output":"local result","finish_reason":"stop","prompt_tokens":10,"completion_tokens":2,"total_tokens":12,"audit_path":"logs/audit/inference.jsonl"},"error":null,"emitted_at":"2026-08-30T00:00:00+00:00"}"#
    let script = """
    #!/bin/sh
    case " $* " in *private-local-prompt*|*runtime-secret*) exit 9;; esac
    [ "$OMLX_API_KEY" = "omlx-runtime-secret" ] || exit 8
    [ "$MAC_AI_WORK_OS_BROKER_TOKEN" = "broker-runtime-secret" ] || exit 7
    [ "$MAC_AI_WORK_OS_MEMORY_TOKEN" = "memory-runtime-secret" ] || exit 6
    body=$(cat)
    case "$body" in *private-local-prompt*) ;; *) exit 5;; esac
    printf '%s' '\(response)'
    """
    try script.write(to: executable, atomically: true, encoding: .utf8)
    try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: executable.path)
    let payload = try SupervisorClient(executableURL: executable).localTask(
        rootURL: temporary.appendingPathComponent("Product"),
        prompt: "private-local-prompt", maximumOutputTokens: 128,
        omlxAPIKey: "omlx-runtime-secret", brokerToken: "broker-runtime-secret",
        memoryToken: "memory-runtime-secret",
        requestID: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
    )
    #expect(payload.route == "local")
    #expect(payload.output == "local result")
    #expect(payload.totalTokens == 12)
}

@Test func localTaskRejectsOversizePromptBeforeLaunchingSupervisor() throws {
    let client = try SupervisorClient(executableURL: URL(fileURLWithPath: "/not/launched"))
    #expect(throws: SupervisorProtocolError.requestTooLarge) {
        try client.localTask(
            rootURL: URL(fileURLWithPath: "/tmp/Product"),
            prompt: String(repeating: "x", count: 262_145), maximumOutputTokens: 1,
            omlxAPIKey: "a", brokerToken: "b", memoryToken: "c"
        )
    }
}

@Test func cloudPreviewRejectsOversizeBodyBeforeLaunchingSupervisor() throws {
    let client = try SupervisorClient(
        executableURL: URL(fileURLWithPath: "/does/not/need/to/exist"), maximumRequestBytes: 3
    )
    #expect(throws: SupervisorProtocolError.requestTooLarge) {
        try client.cloudPreview(
            rootURL: URL(fileURLWithPath: "/tmp/Product"),
            catalogURL: URL(fileURLWithPath: "/tmp/cloud.json"),
            modelID: "deepseek-v4-flash", estimatedInputTokens: 1,
            maximumOutputTokens: 1, minimumAvailableMemoryMB: 1,
            requiredCapabilities: ["chat"], dataClasses: ["user_text"],
            reasonCodes: ["local_validation_failed"], redactions: [],
            outboundBody: Data("four".utf8)
        )
    }
}

@Test(.enabled(if: ProcessInfo.processInfo.environment["MAC_AI_WORK_OS_RUNTIME_INTEGRATION"] == "1"))
func realKeychainRuntimeSampleAuditAndStop() throws {
    guard let supervisorPath = ProcessInfo.processInfo.environment["MAC_AI_WORK_OS_RUNTIME_SUPERVISOR"],
          let rootPath = ProcessInfo.processInfo.environment["MAC_AI_WORK_OS_RUNTIME_ROOT"] else {
        Issue.record("Runtime integration paths are required")
        return
    }
    let supervisor = URL(fileURLWithPath: supervisorPath)
    let root = URL(fileURLWithPath: rootPath, isDirectory: true)
    let client = try SupervisorClient(executableURL: supervisor)
    let secrets = try RuntimeSecretCoordinator().ensure()
    defer { _ = try? client.stopRuntime(rootURL: root) }

    let started = try client.startRuntime(
        rootURL: root,
        omlxAPIKey: secrets.omlxAPIKey,
        brokerToken: secrets.brokerToken,
        memoryToken: secrets.memoryToken
    )
    #expect(started.runtime.phase == "running")
    let status = try client.runtimeStatus(rootURL: root)
    #expect(status.phase == "running")
    #expect(status.omlxAlive)
    #expect(status.brokerAlive)
    #expect(status.memoryAlive == true)

    let correlation = UUID()
    let sample = try client.sampleTask(
        rootURL: root,
        omlxAPIKey: secrets.omlxAPIKey,
        brokerToken: secrets.brokerToken,
        memoryToken: secrets.memoryToken,
        requestID: correlation
    )
    #expect(sample.correlationID == correlation.uuidString.lowercased())
    #expect(!sample.output.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
    let audit = root.appendingPathComponent(sample.auditPath)
    let auditText = try String(contentsOf: audit, encoding: .utf8)
    #expect(auditText.contains(sample.correlationID))
    #expect(!auditText.contains("LOCAL_AI_READY"))
    #expect(!auditText.contains(sample.output))
    #expect(!auditText.contains(secrets.omlxAPIKey))
    #expect(!auditText.contains(secrets.brokerToken))
    #expect(!auditText.contains(secrets.memoryToken))

    let stopped = try client.stopRuntime(rootURL: root)
    #expect(stopped.runtime.phase == "stopped")
}
