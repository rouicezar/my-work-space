import Foundation
import Security

public enum RuntimeSecretError: Error, Equatable, CustomStringConvertible {
    case keychain(OSStatus)
    case invalidExistingSecret(String)
    case duplicateSecrets
    case randomGeneration(OSStatus)

    public var description: String {
        switch self {
        case .keychain(let status): "Keychain operation failed with status \(status)"
        case .invalidExistingSecret(let account): "Existing secret is invalid for \(account)"
        case .duplicateSecrets: "Runtime secrets must be distinct"
        case .randomGeneration(let status): "Secure random generation failed with status \(status)"
        }
    }
}

public protocol SecretStore {
    func read(account: String) throws -> Data?
    func write(_ value: Data, account: String) throws
    func delete(account: String) throws
}

public struct KeychainSecretStore: SecretStore {
    public let service: String

    public init(service: String = "app.mac-ai-work-os.runtime") {
        self.service = service
    }

    public func read(account: String) throws -> Data? {
        var query = baseQuery(account: account)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess, let data = result as? Data else {
            throw RuntimeSecretError.keychain(status)
        }
        return data
    }

    public func write(_ value: Data, account: String) throws {
        let query = baseQuery(account: account)
        let update = [kSecValueData as String: value]
        let updateStatus = SecItemUpdate(query as CFDictionary, update as CFDictionary)
        if updateStatus == errSecSuccess { return }
        guard updateStatus == errSecItemNotFound else {
            throw RuntimeSecretError.keychain(updateStatus)
        }
        var attributes = query
        attributes[kSecValueData as String] = value
        attributes[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        let addStatus = SecItemAdd(attributes as CFDictionary, nil)
        guard addStatus == errSecSuccess else {
            throw RuntimeSecretError.keychain(addStatus)
        }
    }

    public func delete(account: String) throws {
        let status = SecItemDelete(baseQuery(account: account) as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw RuntimeSecretError.keychain(status)
        }
    }

    private func baseQuery(account: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecAttrSynchronizable as String: false,
        ]
    }
}

public struct RuntimeSecrets: CustomStringConvertible, Equatable {
    public let brokerToken: String
    public let memoryToken: String
    public let omlxAPIKey: String

    public var description: String {
        "RuntimeSecrets(brokerToken: <redacted>, memoryToken: <redacted>, omlxAPIKey: <redacted>)"
    }
}

public struct RuntimeSecretCoordinator {
    public static let brokerAccount = "inference-broker-client-token"
    public static let memoryAccount = "governed-memory-client-token"
    public static let omlxAccount = "omlx-api-key"

    private let store: SecretStore
    private let randomToken: () throws -> String

    public init(
        store: SecretStore = KeychainSecretStore(),
        randomToken: @escaping () throws -> String = RuntimeSecretCoordinator.secureToken
    ) {
        self.store = store
        self.randomToken = randomToken
    }

    public func ensure() throws -> RuntimeSecrets {
        let broker = try readOrCreate(account: Self.brokerAccount)
        let memory = try readOrCreate(account: Self.memoryAccount)
        let omlx = try readOrCreate(account: Self.omlxAccount)
        guard Set([broker, memory, omlx]).count == 3 else { throw RuntimeSecretError.duplicateSecrets }
        return RuntimeSecrets(brokerToken: broker, memoryToken: memory, omlxAPIKey: omlx)
    }

    public func deleteAll() throws {
        try store.delete(account: Self.brokerAccount)
        try store.delete(account: Self.memoryAccount)
        try store.delete(account: Self.omlxAccount)
    }

    private func readOrCreate(account: String) throws -> String {
        if let existing = try store.read(account: account) {
            guard let value = String(data: existing, encoding: .utf8), value.count >= 32 else {
                throw RuntimeSecretError.invalidExistingSecret(account)
            }
            return value
        }
        let value = try randomToken()
        guard value.count >= 32 else {
            throw RuntimeSecretError.invalidExistingSecret(account)
        }
        try store.write(Data(value.utf8), account: account)
        return value
    }

    public static func secureToken() throws -> String {
        var bytes = [UInt8](repeating: 0, count: 32)
        let status = SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes)
        guard status == errSecSuccess else {
            throw RuntimeSecretError.randomGeneration(status)
        }
        return Data(bytes)
            .base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
}
