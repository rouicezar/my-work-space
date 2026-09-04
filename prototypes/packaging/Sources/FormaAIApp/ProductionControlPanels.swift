import SwiftUI
import LifecycleContract
import SupervisorProtocol
import RuntimeSecurity

struct LocalRuntimeControlPanel: View {
    let language: ProductLanguage
    @State private var runtimeState: RuntimeViewState = .loading

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text(copy[.localRuntimeTitle]).font(.title2.weight(.semibold))
                Text(copy.productionLocalRuntimeSubtitle).font(.callout).foregroundStyle(.secondary)
                runtimeCard
                HStack(spacing: 10) {
                    Button(copy.startLocalRuntime) { Task { await startRuntime() } }
                        .buttonStyle(.borderedProminent)
                        .disabled(runtimeState.isBusy)
                    Button(copy.stopLocalRuntime) { Task { await stopRuntime() } }
                        .buttonStyle(.bordered)
                        .disabled(runtimeState.isBusy)
                    Button(copy.verifyLocalRuntime) { Task { await runSampleTask() } }
                        .buttonStyle(.bordered)
                        .disabled(runtimeState.isBusy)
                    Button(copy.refreshStatus) { Task { await refresh() } }
                        .buttonStyle(.borderless)
                }
            }
            .padding(28)
            .frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .task { await refresh() }
    }

    @ViewBuilder
    private var runtimeCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label(copy.runtimeCardTitle(runtimeState), systemImage: runtimeSymbol)
                .font(.headline)
                .foregroundStyle(runtimeTint)
            if case .degraded(let message) = runtimeState {
                Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
            }
            if case .failed(let message) = runtimeState {
                Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
            }
            if case .sample(let model, let output, let correlation) = runtimeState {
                Text(copy.localModelRoute(model)).font(.caption).foregroundStyle(.secondary)
                Text(output).font(.callout).textSelection(.enabled)
                Text(copy.auditCorrelation(correlation)).font(.caption2.monospaced()).foregroundStyle(.tertiary)
            }
        }
        .padding(16)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
    }

    private var runtimeSymbol: String {
        switch runtimeState {
        case .running, .sample: "checkmark.circle.fill"
        case .starting, .loading, .sampling: "circle.dotted"
        case .stopped: "stop.circle"
        case .degraded: "exclamationmark.triangle.fill"
        case .failed: "xmark.circle.fill"
        }
    }

    private var runtimeTint: Color {
        switch runtimeState {
        case .running, .sample: .green
        case .starting, .loading, .sampling: .secondary
        case .stopped: .secondary
        case .degraded: .orange
        case .failed: .red
        }
    }

    @MainActor private func refresh() async { await loadRuntimeStatus() }

    @MainActor private func loadRuntimeStatus() async {
        guard let context = ProductPaths.installationContext() else {
            runtimeState = .failed(copy.supervisorUnavailable)
            return
        }
        runtimeState = .loading
        runtimeState = await Task.detached { () -> RuntimeViewState in
            do {
                let status = try SupervisorClient(executableURL: context.supervisor).runtimeStatus(rootURL: context.root)
                guard status.schemaVersion == 1 else { return .failed("Unsupported runtime status.") }
                switch status.phase {
                case "stopped": return .stopped
                case "running" where status.omlxAlive && status.brokerAlive: return .running
                default:
                    return .degraded("phase=\(status.phase), oMLX=\(status.omlxAlive), broker=\(status.brokerAlive)")
                }
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor private func startRuntime() async {
        guard let context = ProductPaths.installationContext() else {
            runtimeState = .failed(copy.supervisorUnavailable)
            return
        }
        runtimeState = .starting
        runtimeState = await Task.detached { () -> RuntimeViewState in
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                let result = try SupervisorClient(executableURL: context.supervisor).startRuntime(
                    rootURL: context.root,
                    osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
                    architecture: ProductPaths.hostArchitecture,
                    omlxAPIKey: secrets.omlxAPIKey,
                    brokerToken: secrets.brokerToken,
                    memoryToken: secrets.memoryToken
                )
                return result.runtime.phase == "running" ? .running : .degraded("Runtime did not reach running.")
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor private func stopRuntime() async {
        guard let context = ProductPaths.installationContext() else {
            runtimeState = .failed(copy.supervisorUnavailable)
            return
        }
        runtimeState = .loading
        runtimeState = await Task.detached { () -> RuntimeViewState in
            do {
                let result = try SupervisorClient(executableURL: context.supervisor).stopRuntime(rootURL: context.root)
                return result.runtime.phase == "stopped" ? .stopped : .failed("Runtime did not stop.")
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor private func runSampleTask() async {
        guard let context = ProductPaths.installationContext() else {
            runtimeState = .failed(copy.supervisorUnavailable)
            return
        }
        runtimeState = .sampling
        runtimeState = await Task.detached { () -> RuntimeViewState in
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                let sample = try SupervisorClient(executableURL: context.supervisor).sampleTask(
                    rootURL: context.root,
                    omlxAPIKey: secrets.omlxAPIKey,
                    brokerToken: secrets.brokerToken,
                    memoryToken: secrets.memoryToken
                )
                guard sample.schemaVersion == 1, !sample.output.isEmpty else {
                    return .failed("Sample result was empty.")
                }
                return .sample(sample.model, sample.output, sample.correlationID)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }
}

struct ModelsProvidersControlPanel: View {
    let language: ProductLanguage
    @StateObject private var preparation = LocalAIPreparationCoordinator()

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text(copy[.modelsProvidersTitle]).font(.title2.weight(.semibold))
                Text(copy.productionModelsSubtitle).font(.callout).foregroundStyle(.secondary)
                modelStatusCard
                HStack(spacing: 10) {
                    Button(copy.prepareLocalModel) {
                        Task { await preparation.retry() }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(preparation.isBusy)
                    Button(copy.refreshStatus) {
                        Task { await preparation.prepareIfNeeded() }
                    }
                    .buttonStyle(.bordered)
                    .disabled(preparation.isBusy)
                }
                Text(copy.productionModelsRouteNote).font(.caption).foregroundStyle(.secondary)
            }
            .padding(28)
            .frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .task { await preparation.prepareIfNeeded() }
    }

    @ViewBuilder
    private var modelStatusCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                if preparation.isBusy { ProgressView().controlSize(.small) }
                Text(FirstRunCopy(language: language).preparationStatus(preparation.status))
                    .font(.callout)
            }
            if let model = preparation.recommendedModelLabel {
                Text(model).font(.caption.monospaced()).foregroundStyle(.secondary)
            }
            if case .downloadingModel(let transferred, let total) = preparation.status, total > 0 {
                ProgressView(value: Double(transferred), total: Double(total))
                Text(copy.downloadProgress(transferred: transferred, total: total))
                    .font(.caption).foregroundStyle(.secondary)
            }
            if case .failed(let message) = preparation.status {
                Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
            }
        }
        .padding(16)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
    }
}

struct DiagnosticsRecoveryControlPanel: View {
    let language: ProductLanguage
    @State private var preflightSummary = "—"
    @State private var installationSummary = "—"
    @State private var isLoading = true

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text(copy[.diagnosticsTitle]).font(.title2.weight(.semibold))
                Text(copy.productionDiagnosticsSubtitle).font(.callout).foregroundStyle(.secondary)
                GroupBox(copy.systemChecks) {
                    VStack(alignment: .leading, spacing: 8) {
                        if isLoading { ProgressView(copy.runningChecks) }
                        detailRow(copy.preflightStatus, preflightSummary)
                        detailRow(copy.installationStatus, installationSummary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                if let context = ProductPaths.installationContext() {
                    HistoryRecoveryPanel(language: language, supervisorURL: context.supervisor, rootURL: context.root)
                } else {
                    Text(copy.supervisorUnavailable).foregroundStyle(.secondary)
                }
            }
            .padding(28)
            .frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .task { await refresh() }
    }

    private func detailRow(_ title: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(title).font(.caption.weight(.semibold)).foregroundStyle(.secondary).frame(width: 130, alignment: .leading)
            Text(value).font(.callout).textSelection(.enabled)
        }
    }

    @MainActor private func refresh() async {
        guard let context = ProductPaths.installationContext() else {
            preflightSummary = copy.supervisorUnavailable
            installationSummary = copy.supervisorUnavailable
            isLoading = false
            return
        }
        isLoading = true
        let result = await Task.detached { () -> (String, String) in
            do {
                let client = try SupervisorClient(executableURL: context.supervisor)
                let profiles = ProductPaths.bundledResourceURL(name: "hardware-profiles", ext: "json")
                    ?? ProductPaths.developmentResourceURL("config/hardware-profiles.json")
                guard let profiles else { throw PreparationFailure(message: "Hardware profiles are missing.") }
                let preflight = try client.preflight(
                    profilesURL: profiles,
                    checkPath: context.root,
                    ports: [8000, 43110, 43111]
                )
                let install = try client.installationStatus(rootURL: context.root)
                let pre = "status=\(preflight.status)"
                let inst: String
                if let op = install.operation {
                    inst = "component=\(install.component), phase=\(op.phase)"
                } else {
                    inst = "component=\(install.component), idle"
                }
                return (pre, inst)
            } catch {
                return (String(describing: error), String(describing: error))
            }
        }.value
        preflightSummary = result.0
        installationSummary = result.1
        isLoading = false
    }
}

private extension RuntimeViewState {
    var isBusy: Bool {
        switch self {
        case .loading, .starting, .sampling: return true
        default: return false
        }
    }
}
