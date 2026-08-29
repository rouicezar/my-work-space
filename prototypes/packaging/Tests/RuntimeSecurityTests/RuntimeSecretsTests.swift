import Foundation
import Testing
@testable import RuntimeSecurity

private final class MemorySecretStore: SecretStore {
    var values: [String: Data] = [:]

    func read(account: String) throws -> Data? { values[account] }
    func write(_ value: Data, account: String) throws { values[account] = value }
    func delete(account: String) throws { values.removeValue(forKey: account) }
}

@Test func createsDistinctSecretsAndReusesThem() throws {
    let store = MemorySecretStore()
    var generated = ["a".padding(toLength: 40, withPad: "a", startingAt: 0),
                     "b".padding(toLength: 40, withPad: "b", startingAt: 0)]
    let coordinator = RuntimeSecretCoordinator(store: store) { generated.removeFirst() }
    let first = try coordinator.ensure()
    let second = try coordinator.ensure()
    #expect(first == second)
    #expect(first.brokerToken != first.omlxAPIKey)
    #expect(store.values.count == 2)
    #expect(String(describing: first) == "RuntimeSecrets(brokerToken: <redacted>, omlxAPIKey: <redacted>)")
    #expect(!String(describing: first).contains(first.brokerToken))
}

@Test func invalidExistingSecretFailsWithoutReplacement() throws {
    let store = MemorySecretStore()
    store.values[RuntimeSecretCoordinator.brokerAccount] = Data("short".utf8)
    let coordinator = RuntimeSecretCoordinator(store: store) {
        "replacement-that-must-never-be-used-123456"
    }
    #expect(throws: RuntimeSecretError.invalidExistingSecret(RuntimeSecretCoordinator.brokerAccount)) {
        try coordinator.ensure()
    }
    #expect(store.values[RuntimeSecretCoordinator.brokerAccount] == Data("short".utf8))
}

@Test func duplicateSecretsFailClosed() throws {
    let store = MemorySecretStore()
    let duplicate = "same-secret-value-with-at-least-32-characters"
    store.values[RuntimeSecretCoordinator.brokerAccount] = Data(duplicate.utf8)
    store.values[RuntimeSecretCoordinator.omlxAccount] = Data(duplicate.utf8)
    #expect(throws: RuntimeSecretError.duplicateSecrets) {
        try RuntimeSecretCoordinator(store: store).ensure()
    }
}

@Test func explicitDeleteRemovesBothRuntimeSecrets() throws {
    let store = MemorySecretStore()
    store.values[RuntimeSecretCoordinator.brokerAccount] = Data("a".utf8)
    store.values[RuntimeSecretCoordinator.omlxAccount] = Data("b".utf8)
    try RuntimeSecretCoordinator(store: store).deleteAll()
    #expect(store.values.isEmpty)
}

@Test func secureTokensHaveSufficientEntropyAndURLSafeEncoding() throws {
    let first = try RuntimeSecretCoordinator.secureToken()
    let second = try RuntimeSecretCoordinator.secureToken()
    #expect(first.count >= 43)
    #expect(first != second)
    #expect(first.allSatisfy { $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_" })
}

@Test(.enabled(if: ProcessInfo.processInfo.environment["MAC_AI_WORK_OS_KEYCHAIN_INTEGRATION"] == "1"))
func realTemporaryKeychainRoundTripAndCleanup() throws {
    let service = "app.mac-ai-work-os.test.\(UUID().uuidString)"
    let account = "round-trip"
    let store = KeychainSecretStore(service: service)
    defer { try? store.delete(account: account) }

    #expect(try store.read(account: account) == nil)
    try store.write(Data("first-test-value".utf8), account: account)
    #expect(try store.read(account: account) == Data("first-test-value".utf8))
    try store.write(Data("updated-test-value".utf8), account: account)
    #expect(try store.read(account: account) == Data("updated-test-value".utf8))
    try store.delete(account: account)
    #expect(try store.read(account: account) == nil)
}
