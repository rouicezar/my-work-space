import Foundation
import Testing
@testable import LifecycleContract

@Test func manifestArgumentRequiresItsNamedFlagAndIgnoresMacOSLaunchArguments() {
    #expect(ManifestArgumentResolver.explicitManifestPath(
        in: ["app", "-ApplePersistenceIgnoreState", "YES"]
    ) == nil)
    #expect(ManifestArgumentResolver.explicitManifestPath(
        in: ["app", "--manifest", "/tmp/product-manifest.json", "-ApplePersistenceIgnoreState", "YES"]
    ) == "/tmp/product-manifest.json")
    #expect(ManifestArgumentResolver.explicitManifestPath(
        in: ["app", "--manifest", "-ApplePersistenceIgnoreState"]
    ) == nil)
}

private func repositoryRoot() -> URL {
    URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
}

@Test func firstScreenIsARealTaskComposerInsteadOfSetupOrRecovery() {
    let contract = WorkbenchSurfaceContract.productDefault

    #expect(contract.initialDestination == .newTask)
    #expect(contract.composerPlacement == .firstScreen)
    #expect(contract.taskSubmissionBinding == .supervisorUnifiedTask)
    #expect(contract.setupAndRecoveryPlacement == .separateSettings)
}

@Test func realProductManifestLoadsAndOrdersComponents() throws {
    let manifestURL = repositoryRoot().appending(path: "config/product-manifest.json")
    let manifest = try ProductManifest.load(from: manifestURL)
    #expect(manifest.startPlan.map(\.id) == ["omlx", "semantica", "herdr", "holaos"])
    #expect(manifest.stopPlan.map(\.id) == ["holaos", "herdr", "semantica", "omlx"])
}

@Test func launcherSummaryExposesPortsAndContractStatus() throws {
    let manifestURL = repositoryRoot().appending(path: "config/product-manifest.json")
    let summary = LauncherSummary(manifest: try ProductManifest.load(from: manifestURL))
    #expect(summary.status == "contract-valid")
    #expect(summary.ports == [
        "omlx": 8000,
        "inference-broker": 43110,
        "governed-memory-service": 43111,
    ])
}

@Test func duplicatePortIsRejected() throws {
    let manifestURL = repositoryRoot().appending(path: "config/product-manifest.json")
    var object = try #require(
        JSONSerialization.jsonObject(with: Data(contentsOf: manifestURL)) as? [String: Any]
    )
    var components = try #require(object["components"] as? [[String: Any]])
    components[1]["port"] = 8000
    object["components"] = components
    let invalid = try JSONSerialization.data(withJSONObject: object)

    #expect(throws: ManifestValidationError.duplicatePort(8000)) {
        try ProductManifest(data: invalid)
    }
}

@Test func productServicePortCollisionIsRejected() throws {
    let manifestURL = repositoryRoot().appending(path: "config/product-manifest.json")
    var object = try #require(
        JSONSerialization.jsonObject(with: Data(contentsOf: manifestURL)) as? [String: Any]
    )
    var services = try #require(object["product_services"] as? [[String: Any]])
    services[1]["port"] = 43110
    object["product_services"] = services
    let invalid = try JSONSerialization.data(withJSONObject: object)

    #expect(throws: ManifestValidationError.duplicatePort(43110)) {
        try ProductManifest(data: invalid)
    }
}

@Test func holaOSBundlingIsRejected() throws {
    let manifestURL = repositoryRoot().appending(path: "config/product-manifest.json")
    var object = try #require(
        JSONSerialization.jsonObject(with: Data(contentsOf: manifestURL)) as? [String: Any]
    )
    var components = try #require(object["components"] as? [[String: Any]])
    let index = try #require(components.firstIndex { $0["id"] as? String == "holaos" })
    components[index]["install_mode"] = "bundled"
    object["components"] = components
    let invalid = try JSONSerialization.data(withJSONObject: object)

    #expect(throws: ManifestValidationError.holaOSDistributionBoundaryLost("bundled")) {
        try ProductManifest(data: invalid)
    }
}
