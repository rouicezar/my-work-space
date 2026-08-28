import Foundation
import LifecycleContract

struct LauncherArguments {
    let manifestURL: URL

    init(arguments: [String]) throws {
        guard arguments.count == 3, arguments[1] == "--manifest" else {
            throw LauncherError.usage
        }
        manifestURL = URL(fileURLWithPath: arguments[2]).standardizedFileURL
    }
}

enum LauncherError: Error, CustomStringConvertible {
    case usage

    var description: String {
        "usage: mac-ai-work-os-launcher --manifest /path/to/product-manifest.json"
    }
}

do {
    let arguments = try LauncherArguments(arguments: CommandLine.arguments)
    let manifest = try ProductManifest.load(from: arguments.manifestURL)
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    FileHandle.standardOutput.write(try encoder.encode(LauncherSummary(manifest: manifest)))
    FileHandle.standardOutput.write(Data("\n".utf8))
} catch {
    FileHandle.standardError.write(Data("error: \(error)\n".utf8))
    exit(2)
}
