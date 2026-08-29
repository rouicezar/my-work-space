import SwiftUI
import LifecycleContract
import SupervisorProtocol

@main
struct MacAIWorkOSPrototypeApp: App {
    var body: some Scene {
        WindowGroup("Mac AI Work OS") {
            ManifestOverview()
                .frame(
                    minWidth: 620,
                    idealWidth: 720,
                    maxWidth: 800,
                    minHeight: 440,
                    idealHeight: 560,
                    maxHeight: 700
                )
        }
        .windowResizability(.contentSize)
    }
}

struct ManifestOverview: View {
    @State private var result: Result<ProductManifest, Error>?
    @State private var supervisorState: SupervisorViewState = .loading
    @State private var installationState: InstallationViewState = .loading

    var body: some View {
        ScrollView {
        VStack(alignment: .leading, spacing: 18) {
            Text("Mac AI Work OS")
                .font(.largeTitle.bold())
            Text("Alpha setup assistant")
                .foregroundStyle(.secondary)

            supervisorSection
            installationSection

            switch result {
            case .success(let manifest):
                Label("Lifecycle contract valid", systemImage: "checkmark.shield.fill")
                    .foregroundStyle(.green)
                    .accessibilityLabel("Lifecycle contract is valid")
                Text("Manifest \(manifest.manifestVersion)")
                ForEach(manifest.startPlan) { component in
                    HStack {
                        Text(component.id)
                            .font(.headline)
                        Spacer()
                        Text(component.version)
                        Text(component.healthContract)
                            .foregroundStyle(.secondary)
                    }
                    .accessibilityElement(children: .combine)
                }
                Text("Components are installed only after an explicit first-run approval.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            case .failure(let error):
                Label("Manifest unavailable", systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
                Text(String(describing: error))
                    .textSelection(.enabled)
            case nil:
                ProgressView("Validating product contract…")
            }
            Spacer()
        }
        .padding(24)
        }
        .task {
            loadManifest()
            await loadSupervisorPreflight()
            await loadInstallationPlan()
        }
    }

    @ViewBuilder
    private var installationSection: some View {
        GroupBox("Local inference setup") {
            VStack(alignment: .leading, spacing: 8) {
                switch installationState {
                case .loading:
                    ProgressView("Preparing exact installation plan…")
                case .unavailable(let message):
                    Label("Installation plan unavailable", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text(message).font(.callout).foregroundStyle(.secondary)
                case .planned(let plan):
                    Label(
                        plan.alreadyActive ? "oMLX is already active" : "oMLX \(plan.release) is ready to install",
                        systemImage: plan.alreadyActive ? "checkmark.circle.fill" : "arrow.down.circle"
                    )
                    .foregroundStyle(plan.alreadyActive ? .green : .primary)
                    Text("Download: \(byteCount(plan.artifactSizeBytes - plan.downloadedBytes)) remaining of \(byteCount(plan.artifactSizeBytes))")
                    Text("Destination: \(plan.productRoot)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .textSelection(.enabled)
                    if !plan.alreadyActive {
                        Button("Approve and install oMLX") {
                            Task { await install(plan) }
                        }
                        .buttonStyle(.borderedProminent)
                        .accessibilityHint("Downloads the pinned oMLX artifact and installs it into the displayed destination")
                    }
                case .installing(let step):
                    ProgressView(step)
                    Text("Closing the app does not corrupt completed steps; reopening can resume the operation.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                case .installed(let release):
                    Label("oMLX \(release) installed", systemImage: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                case .failed(let message):
                    Label("Installation stopped safely", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.red)
                    Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                    Button("Review plan and resume") {
                        Task { await loadInstallationPlan() }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func loadManifest() {
        let explicitPath = CommandLine.arguments.dropFirst().first
        let explicitURL = explicitPath.map { URL(fileURLWithPath: $0) }
        let bundledURL = Bundle.main.url(forResource: "product-manifest", withExtension: "json")
        let developmentURL = URL(
            fileURLWithPath: FileManager.default.currentDirectoryPath + "/config/product-manifest.json"
        )
        result = Result {
            try ProductManifest.load(from: explicitURL ?? bundledURL ?? developmentURL)
        }
    }

    @ViewBuilder
    private var supervisorSection: some View {
        GroupBox("Setup readiness") {
            VStack(alignment: .leading, spacing: 8) {
                switch supervisorState {
                case .loading:
                    ProgressView("Requesting authoritative preflight…")
                case .unavailable(let message):
                    Label("Supervisor unavailable", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text(message).font(.callout).foregroundStyle(.secondary)
                case .ready(let report):
                    Label(preflightTitle(report.status), systemImage: preflightIcon(report.status))
                        .foregroundStyle(preflightColor(report.status))
                        .font(.headline)
                    if let profile = report.selectedProfile {
                        Text(profile.label)
                        Text("Provisional profile: \(profile.id)")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    ForEach(report.blockers + report.unknowns) { finding in
                        Text("\(finding.code): \(finding.message)")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    Text(report.notice).font(.caption).foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @MainActor
    private func loadSupervisorPreflight() async {
        guard let supervisor = supervisorExecutableURL() else {
            supervisorState = .unavailable(
                "This development bundle does not contain a self-contained Supervisor helper."
            )
            return
        }
        guard let profiles = Bundle.main.url(
            forResource: "hardware-profiles", withExtension: "json"
        ) ?? developmentProfilesURL() else {
            supervisorState = .unavailable("Hardware profiles are missing from the app resources.")
            return
        }
        let checkPath = FileManager.default.homeDirectoryForCurrentUser
        let outcome = await Task.detached { () -> SupervisorViewState in
            do {
                let client = try SupervisorClient(executableURL: supervisor)
                return .ready(try client.preflight(
                    profilesURL: profiles,
                    checkPath: checkPath,
                    ports: [8000]
                ))
            } catch {
                return .unavailable(String(describing: error))
            }
        }.value
        supervisorState = outcome
    }

    @MainActor
    private func loadInstallationPlan() async {
        guard let context = installationContext() else {
            installationState = .unavailable("Supervisor or pinned upstream manifest is missing.")
            return
        }
        installationState = .loading
        installationState = await Task.detached { () -> InstallationViewState in
            do {
                let client = try SupervisorClient(executableURL: context.supervisor)
                let plan = try client.installationPlan(
                    rootURL: context.root,
                    osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
                    upstreamsURL: context.upstreams
                )
                guard plan.schemaVersion == 1, plan.component == "omlx", plan.approvalRequired,
                      plan.artifactSizeBytes > 0, plan.downloadedBytes >= 0,
                      plan.downloadedBytes <= plan.artifactSizeBytes,
                      plan.artifactSHA256.count == 64 else {
                    return .unavailable("Supervisor returned an invalid installation plan.")
                }
                return .planned(plan)
            } catch {
                return .unavailable(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func install(_ plan: InstallationPlanPayload) async {
        guard let context = installationContext() else {
            installationState = .failed("Supervisor or pinned upstream manifest is missing.")
            return
        }
        installationState = .installing("Downloading, verifying, and activating oMLX…")
        installationState = await Task.detached { () -> InstallationViewState in
            do {
                let client = try SupervisorClient(executableURL: context.supervisor)
                let installed = try client.installOMLX(
                    rootURL: context.root,
                    osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
                    upstreamsURL: context.upstreams,
                    approvedArtifactSHA256: plan.artifactSHA256
                )
                guard installed.schemaVersion == 1 else {
                    return .failed("Supervisor returned an unsupported installation result.")
                }
                return .installed(installed.active.release)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    private func installationContext() -> InstallationContext? {
        guard let supervisor = supervisorExecutableURL(),
              let upstreams = Bundle.main.url(forResource: "upstreams", withExtension: "json")
                ?? developmentUpstreamsURL(),
              let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
        else { return nil }
        return InstallationContext(
            supervisor: supervisor,
            upstreams: upstreams,
            root: support.appendingPathComponent("Mac AI Work OS", isDirectory: true)
        )
    }

    private func developmentUpstreamsURL() -> URL? {
        let url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
            .appendingPathComponent("config/upstreams.json")
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    private func byteCount(_ count: Int64) -> String {
        ByteCountFormatter.string(fromByteCount: max(0, count), countStyle: .file)
    }

    private func supervisorExecutableURL() -> URL? {
        let bundled = Bundle.main.bundleURL
            .appendingPathComponent("Contents/Helpers/Supervisor", isDirectory: true)
            .appendingPathComponent("mac-ai-work-os-supervisor", isDirectory: false)
        if FileManager.default.isExecutableFile(atPath: bundled.path) {
            return bundled
        }
        guard let path = ProcessInfo.processInfo.environment["MAC_AI_WORK_OS_SUPERVISOR"],
              path.hasPrefix("/") else {
            return nil
        }
        return URL(fileURLWithPath: path)
    }

    private func developmentProfilesURL() -> URL? {
        let url = URL(
            fileURLWithPath: FileManager.default.currentDirectoryPath
        ).appendingPathComponent("config/hardware-profiles.yaml")
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    private func preflightTitle(_ status: String) -> String {
        switch status {
        case "supported": "Hardware preflight passed"
        case "unknown": "Hardware compatibility is unknown"
        default: "This Mac is not currently supported"
        }
    }

    private func preflightIcon(_ status: String) -> String {
        switch status {
        case "supported": "checkmark.circle.fill"
        case "unknown": "questionmark.circle.fill"
        default: "xmark.octagon.fill"
        }
    }

    private func preflightColor(_ status: String) -> Color {
        switch status {
        case "supported": .green
        case "unknown": .orange
        default: .red
        }
    }
}

private enum SupervisorViewState: Sendable {
    case loading
    case unavailable(String)
    case ready(PreflightPayload)
}

private struct InstallationContext: Sendable {
    let supervisor: URL
    let upstreams: URL
    let root: URL
}

private enum InstallationViewState: Sendable {
    case loading
    case unavailable(String)
    case planned(InstallationPlanPayload)
    case installing(String)
    case installed(String)
    case failed(String)
}
