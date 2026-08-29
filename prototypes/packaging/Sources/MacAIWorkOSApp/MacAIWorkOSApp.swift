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

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Mac AI Work OS")
                .font(.largeTitle.bold())
            Text("Packaging architecture prototype")
                .foregroundStyle(.secondary)

            supervisorSection

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
                Text("No component is installed or started by this prototype.")
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
        .task {
            loadManifest()
            await loadSupervisorPreflight()
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
