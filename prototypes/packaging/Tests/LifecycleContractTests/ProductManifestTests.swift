import Foundation
import Testing
@testable import LifecycleContract

private func repositoryRoot() -> URL {
    URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
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
    #expect(summary.ports == ["omlx": 8000, "semantica": 8765])
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
