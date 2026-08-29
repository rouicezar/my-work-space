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
