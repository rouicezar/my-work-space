import Foundation
import SupervisorProtocol

enum ProductPaths {
    static let productFolderName = "Forma AI"
    static let modelCacheFolderName = "model-cache"

    static func applicationSupportRoot() -> URL? {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
    }

    static func productRootURL() -> URL? {
        guard let support = applicationSupportRoot() else { return nil }
        return support.appendingPathComponent(productFolderName, isDirectory: true)
    }

    static func modelCacheRootURL() throws -> URL {
        guard let productRoot = productRootURL() else {
            throw PreparationFailure(message: "Application Support is unavailable.")
        }
        let cache = productRoot.appendingPathComponent(modelCacheFolderName, isDirectory: true)
        try FileManager.default.createDirectory(at: cache, withIntermediateDirectories: true)
        return cache
    }

    static func supervisorExecutableURL(bundle: Bundle = .main) -> URL? {
        let bundled = bundle.bundleURL
            .appendingPathComponent("Contents/Helpers/Supervisor", isDirectory: true)
            .appendingPathComponent("forma-ai-supervisor", isDirectory: false)
        if FileManager.default.isExecutableFile(atPath: bundled.path) {
            return bundled
        }
        let dev = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
            .appendingPathComponent("prototypes/packaging/.build/debug/forma-ai-supervisor")
        return FileManager.default.fileExists(atPath: dev.path) ? dev : nil
    }

    static func bundledResourceURL(name: String, ext: String) -> URL? {
        Bundle.main.url(forResource: name, withExtension: ext)
    }

    static func developmentResourceURL(_ relative: String) -> URL? {
        let url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent(relative)
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    static func installationContext() -> InstallationContext? {
        guard let supervisor = supervisorExecutableURL(),
              let upstreams = bundledResourceURL(name: "upstreams", ext: "json")
                ?? developmentResourceURL("config/upstreams.json"),
              let root = productRootURL()
        else { return nil }
        return InstallationContext(supervisor: supervisor, upstreams: upstreams, root: root)
    }

    static func modelContext() -> ModelContext? {
        guard let installation = installationContext(),
              let catalog = bundledResourceURL(name: "models", ext: "json")
                ?? developmentResourceURL("config/models.json")
        else { return nil }
        guard let cache = try? modelCacheRootURL() else { return nil }
        return ModelContext(
            supervisor: installation.supervisor,
            root: installation.root,
            cacheRoot: cache,
            catalog: catalog
        )
    }

    static func taskContext(evidenceRelative: String = ".") -> TaskContext? {
        guard let installation = installationContext(),
              let models = bundledResourceURL(name: "models", ext: "json")
                ?? developmentResourceURL("config/models.json"),
              let hardware = bundledResourceURL(name: "hardware-profiles", ext: "json")
                ?? developmentResourceURL("config/hardware-profiles.yaml"),
              let localProfiles = bundledResourceURL(name: "local-model-profiles", ext: "json")
                ?? developmentResourceURL("config/local-model-profiles.json"),
              let cloud = bundledResourceURL(name: "cloud-providers", ext: "json")
                ?? developmentResourceURL("config/cloud-providers.json")
        else { return nil }
        let evidenceRoot = bundledResourceURL(name: "local-model-profiles", ext: "json")
            .map { $0.deletingLastPathComponent() }
            ?? developmentResourceURL(evidenceRelative)
        guard let evidenceRoot else { return nil }
        return TaskContext(
            supervisor: installation.supervisor,
            root: installation.root,
            models: models,
            hardware: hardware,
            localProfiles: localProfiles,
            cloud: cloud,
            evidenceRoot: evidenceRoot
        )
    }

    static var hostArchitecture: String {
        #if arch(arm64)
        return "aarch64"
        #elseif arch(x86_64)
        return "x86_64"
        #else
        return "unknown"
        #endif
    }
}
