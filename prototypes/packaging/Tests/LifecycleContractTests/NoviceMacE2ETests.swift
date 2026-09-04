import Testing
import Foundation

@Test func firstRunGateRequiresReadyInSource() throws {
    let source = try String(contentsOf: packagingSource("FirstRunAssistantView.swift"), encoding: .utf8)
    #expect(source.contains("preparation.isReady"))
    #expect(source.contains("canAdvancePrimary"))
    #expect(source.contains("downloadingModel"))
}

@Test func productionSettingsUseRealControlPanels() throws {
    let source = try String(contentsOf: packagingSource("DailyWorkbenchShell.swift"), encoding: .utf8)
    #expect(source.contains("LocalRuntimeControlPanel"))
    #expect(source.contains("ModelsProvidersControlPanel"))
    #expect(source.contains("DiagnosticsRecoveryControlPanel"))
}

@Test func modelCacheUsesApplicationSupportNotHuggingFaceDefault() throws {
    let source = try String(contentsOf: packagingSource("ProductPaths.swift"), encoding: .utf8)
    #expect(source.contains("model-cache"))
    #expect(!source.contains(".cache/huggingface"))
}

@Test func preparationPipelineDownloadsWhenModelMissing() throws {
    let source = try String(contentsOf: packagingSource("LocalAIPreparationCoordinator.swift"), encoding: .utf8)
    #expect(source.contains("downloadingModel"))
    #expect(source.contains("ModelDownloadCoordinator"))
    #expect(source.contains("ModelDownloadCoordinator.downloadChatModel"))
}

@Test func supervisorClientExposesDownloadModelCommand() throws {
    let source = try String(contentsOf: supervisorSource(), encoding: .utf8)
    #expect(source.contains("download-model"))
    #expect(source.contains("func downloadModel"))
}

private func packagingSource(_ name: String) -> URL {
    URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .appendingPathComponent("Sources/FormaAIApp/\(name)")
}

private func supervisorSource() -> URL {
    URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .appendingPathComponent("Sources/SupervisorProtocol/SupervisorProtocol.swift")
}
