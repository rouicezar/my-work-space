import Foundation
import Testing
@testable import FormaAIApp

@Test func bundledSupervisorResolvesFromContentsHelpers() throws {
    let temporaryRoot = FileManager.default.temporaryDirectory
        .appendingPathComponent("forma-ai-product-paths-\(UUID().uuidString)", isDirectory: true)
    defer { try? FileManager.default.removeItem(at: temporaryRoot) }

    let app = temporaryRoot.appendingPathComponent("Forma AI.app", isDirectory: true)
    let contents = app.appendingPathComponent("Contents", isDirectory: true)
    let helperDirectory = contents.appendingPathComponent("Helpers/Supervisor", isDirectory: true)
    let resources = contents.appendingPathComponent("Resources", isDirectory: true)
    try FileManager.default.createDirectory(at: helperDirectory, withIntermediateDirectories: true)
    try FileManager.default.createDirectory(at: resources, withIntermediateDirectories: true)
    let info = """
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0"><dict>
      <key>CFBundleIdentifier</key><string>dev.formaai.path-test</string>
      <key>CFBundleName</key><string>Forma AI</string>
      <key>CFBundlePackageType</key><string>APPL</string>
    </dict></plist>
    """
    try info.write(to: contents.appendingPathComponent("Info.plist"), atomically: true, encoding: .utf8)

    let helper = helperDirectory.appendingPathComponent("forma-ai-supervisor")
    try Data("#!/bin/sh\nexit 0\n".utf8).write(to: helper)
    try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: helper.path)

    let bundle = try #require(Bundle(url: app))
    #expect(ProductPaths.supervisorExecutableURL(bundle: bundle)?.standardizedFileURL == helper.standardizedFileURL)
}
