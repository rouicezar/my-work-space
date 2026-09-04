import Foundation
import SupervisorProtocol

struct ModelDownloadProgress: Sendable, Equatable {
    let transferredBytes: Int64
    let totalBytes: Int64
    let modelID: String
}

enum ModelDownloadOutcome: Sendable {
    case completed(ModelDownloadProgress)
    case failed(String)
}

enum ModelDownloadCoordinator {
    static func downloadChatModel(
        context: ModelContext,
        approvedRevision: String,
        onProgress: @Sendable @escaping (ModelDownloadProgress) -> Void
    ) async -> ModelDownloadOutcome {
        await Task.detached {
            do {
                let client = try SupervisorClient(executableURL: context.supervisor)
                let payload = try client.downloadModel(
                    rootURL: context.root,
                    cacheRootURL: context.cacheRoot,
                    catalogURL: context.catalog,
                    approvedRevision: approvedRevision
                )
                guard payload.schemaVersion == 1,
                      payload.revision == approvedRevision,
                      payload.totalSizeBytes > 0 else {
                    return ModelDownloadOutcome.failed("Supervisor returned an invalid model download result.")
                }
                let progress = ModelDownloadProgress(
                    transferredBytes: payload.transferredBytes,
                    totalBytes: payload.totalSizeBytes,
                    modelID: payload.modelID
                )
                onProgress(progress)
                return ModelDownloadOutcome.completed(progress)
            } catch {
                return ModelDownloadOutcome.failed(userFacingDownloadError(error))
            }
        }.value
    }

    private static func userFacingDownloadError(_ error: Error) -> String {
        let text = String(describing: error)
        if text.localizedCaseInsensitiveContains("network") || text.localizedCaseInsensitiveContains("url") {
            return "Model download failed. Check your network connection and try again."
        }
        if text.localizedCaseInsensitiveContains("MODEL_CACHE") {
            return "Model storage could not be prepared on this Mac."
        }
        return "Model download failed: \(text)"
    }
}
