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
