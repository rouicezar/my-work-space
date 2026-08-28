import SwiftUI
import LifecycleContract

@main
struct MacAIWorkOSPrototypeApp: App {
    var body: some Scene {
        WindowGroup("Mac AI Work OS") {
            ManifestOverview()
                .frame(minWidth: 620, minHeight: 440)
        }
        .windowResizability(.contentSize)
    }
}

struct ManifestOverview: View {
    @State private var result: Result<ProductManifest, Error>?

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Mac AI Work OS")
                .font(.largeTitle.bold())
            Text("Packaging architecture prototype")
                .foregroundStyle(.secondary)

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
        .task { loadManifest() }
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
}
