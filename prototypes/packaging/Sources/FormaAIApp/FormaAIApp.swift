import SwiftUI
import LifecycleContract
import SupervisorProtocol
import RuntimeSecurity

@main
struct FormaAIPrototypeApp: App {
    var body: some Scene {
        WindowGroup("Forma AI") {
            ManifestOverview()
                .frame(
                    minWidth: 900,
                    idealWidth: 1120,
                    minHeight: 620,
                    idealHeight: 760
                )
        }
    }
}

struct ManifestOverview: View {
    private let surfaceContract: WorkbenchSurfaceContract
    @State private var section: WorkspaceSection?
    @State private var selectedModelChoice: ModelRouteChoice
    @State private var prompt = ""
    @State private var currentTaskPrompt = ""
    @State private var taskState: WorkbenchTaskState = .idle
    @State private var cloudSetupState: CloudSetupViewState = .loading
    @State private var deepSeekAPIKey = ""
    @State private var result: Result<ProductManifest, Error>?
    @State private var supervisorState: SupervisorViewState = .loading
    @State private var installationState: InstallationViewState = .loading
    @State private var modelState: ModelViewState = .loading
    @State private var embeddingState: EmbeddingViewState = .loading
    @State private var runtimeState: RuntimeViewState = .loading

    init(surfaceContract: WorkbenchSurfaceContract = .productDefault) {
        self.surfaceContract = surfaceContract
        _section = State(initialValue: WorkspaceSection(surfaceContract.initialDestination))
        _selectedModelChoice = State(initialValue: surfaceContract.modelSelection.defaultChoice)
    }

    var body: some View {
        NavigationSplitView {
            List(selection: $section) {
                Section {
                    Label("New task", systemImage: "square.and.pencil")
                        .tag(WorkspaceSection.newTask)
                    Label("History", systemImage: "clock.arrow.circlepath")
                        .tag(WorkspaceSection.history)
                }
                Section {
                    Label("Settings & recovery", systemImage: "gearshape")
                        .tag(WorkspaceSection.settings)
                }
            }
            .navigationSplitViewColumnWidth(min: 190, ideal: 220, max: 260)
            .safeAreaInset(edge: .bottom) {
                HStack(spacing: 8) {
                    Circle().fill(runtimeIndicatorColor).frame(width: 8, height: 8)
                    Text(runtimeIndicatorTitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
                .padding(14)
            }
        } detail: {
            switch section ?? .newTask {
            case .newTask: workbench
            case .history: history
            case .settings: setupAssistant
            }
        }
        .task {
            loadManifest()
            await loadSupervisorPreflight()
            await loadInstallationPlan()
            await loadModelPlan()
            await loadEmbeddingPlan()
            await loadRuntimeStatus()
            await loadCloudSettings()
        }
    }

    private var workbench: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("New task").font(.title2.weight(.semibold))
                    Text("Private by default · cloud use always asks first")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                routeBadge
            }
            .padding(.horizontal, 28).padding(.vertical, 18)
            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    switch taskState {
                    case .idle:
                        VStack(spacing: 14) {
                            Image(systemName: "sparkles.rectangle.stack")
                                .font(.system(size: 34, weight: .light))
                                .foregroundStyle(.secondary)
                            Text("What would you like to work on?")
                                .font(.title3.weight(.medium))
                            Text("Ask a question, draft something, or start a task. The workbench keeps local work on this Mac whenever the verified local route can handle it.")
                                .multilineTextAlignment(.center)
                                .foregroundStyle(.secondary)
                                .frame(maxWidth: 520)
                        }
                        .frame(maxWidth: .infinity, minHeight: 360)
                    case .submitting(let text):
                        taskBubble(text)
                        HStack(spacing: 10) {
                            ProgressView()
                            Text("Checking the safest available route…")
                                .foregroundStyle(.secondary)
                        }
                    case .localResult(let text, let model, let correlation):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: "Completed locally", icon: "checkmark.circle.fill", color: .green) {
                            Text(text).textSelection(.enabled)
                            metadata("Local model · \(model)", correlation: correlation)
                        }
                    case .cloudProposal(let proposal):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: "Your approval is required", icon: "lock.shield.fill", color: .orange) {
                            Text("This task is outside the verified local boundary. Nothing has left this Mac.")
                            Grid(alignment: .leading, horizontalSpacing: 18, verticalSpacing: 8) {
                                GridRow { Text("Would send").foregroundStyle(.secondary); Text("\(proposal.payloadSizeBytes) bytes to \(proposal.modelID)") }
                                GridRow { Text("Data").foregroundStyle(.secondary); Text(proposal.dataClasses.joined(separator: ", ")) }
                                GridRow { Text("Location").foregroundStyle(.secondary); Text(proposal.processingLocation) }
                                GridRow { Text("Maximum cost").foregroundStyle(.secondary); Text(String(format: "$%.6f", proposal.estimatedCost.maximum)) }
                            }
                            Text("Cloud approval and execution will be enabled only after a user-provided credential is configured in Settings.")
                                .font(.callout).foregroundStyle(.secondary)
                            HStack {
                                Button("Approve and run") { Task { await approveAndExecute(proposal) } }
                                    .buttonStyle(.borderedProminent)
                                Button("Don't send", role: .cancel) { Task { await rejectProposal(proposal) } }
                            }
                            metadata("Proposal only · no network request", correlation: proposal.correlationID)
                        }
                    case .cloudExecuting:
                        taskBubble(currentTaskPrompt)
                        resultCard(title: "Running approved cloud task", icon: "arrow.up.forward.circle.fill", color: .blue) {
                            ProgressView("Sending only the approved payload and validating the response…")
                        }
                    case .cloudResult(let text, let model, let cost, let correlation):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: "Completed with approved cloud use", icon: "checkmark.shield.fill", color: .green) {
                            Text(text).textSelection(.enabled)
                            Text("Actual cost · \(String(format: "$%.6f", cost))")
                                .font(.caption).foregroundStyle(.secondary)
                            metadata("Approved cloud · \(model)", correlation: correlation)
                        }
                    case .denied:
                        taskBubble(currentTaskPrompt)
                        resultCard(title: "Cloud request not sent", icon: "hand.raised.fill", color: .secondary) {
                            Text("You declined this proposal. Its pending payload was removed.")
                        }
                    case .unavailable(let message):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: "This task cannot run safely", icon: "exclamationmark.triangle.fill", color: .orange) {
                            Text(message)
                            Button("Open recovery settings") { section = .settings }
                        }
                    case .failed(let message):
                        if !currentTaskPrompt.isEmpty { taskBubble(currentTaskPrompt) }
                        resultCard(title: "Task stopped safely", icon: "xmark.octagon.fill", color: .red) {
                            Text(message).textSelection(.enabled)
                        }
                    }
                }
                .padding(28)
            }

            composer
        }
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var composer: some View {
        VStack(spacing: 10) {
            HStack(spacing: 8) {
                Label("Model route", systemImage: "cpu")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Picker("Model route", selection: $selectedModelChoice) {
                    ForEach(surfaceContract.modelSelection.availableChoices) { choice in
                        Text(choice.title).tag(choice)
                    }
                }
                .labelsHidden()
                .pickerStyle(.menu)
                .fixedSize()
                Spacer()
                Text(selectedModelChoice.bindingStatus)
                    .font(.caption2)
                    .foregroundStyle(selectedModelChoice.isExecutionBound ? Color.secondary : Color.orange)
            }
            HStack(alignment: .bottom, spacing: 12) {
                TextField("Message Forma AI", text: $prompt, axis: .vertical)
                    .textFieldStyle(.plain)
                    .lineLimit(1...8)
                    .onSubmit { submitWorkbenchTask() }
                Button { submitWorkbenchTask() } label: {
                    Image(systemName: "arrow.up")
                        .font(.headline).frame(width: 30, height: 30)
                }
                .buttonStyle(.borderedProminent)
                .buttonBorderShape(.circle)
                .disabled(
                    prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                        || taskState.isBusy
                        || !selectedModelChoice.isExecutionBound
                )
                .accessibilityLabel("Submit task")
            }
            .padding(14)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(.separator.opacity(0.7)))
            Text(selectedModelChoice.safetyDescription)
                .font(.caption2).foregroundStyle(.tertiary)
        }
        .padding(.horizontal, 28).padding(.bottom, 22)
    }

    private var history: some View {
        ContentUnavailableView(
            "No task history yet", systemImage: "clock.arrow.circlepath",
            description: Text("Completed and interrupted tasks will appear here with their audit status.")
        )
        .navigationTitle("History")
    }

    private var setupAssistant: some View {
        ScrollView {
        VStack(alignment: .leading, spacing: 18) {
            Text("Settings & recovery")
                .font(.largeTitle.bold())
            Text("Installation, local runtime, models, and advanced diagnostics")
                .foregroundStyle(.secondary)

            supervisorSection
            cloudSettingsSection
            installationSection
            modelSection
            embeddingSection
            runtimeSection

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
    }

    @ViewBuilder
    private var cloudSettingsSection: some View {
        GroupBox("Optional cloud AI") {
            VStack(alignment: .leading, spacing: 10) {
                switch cloudSetupState {
                case .loading:
                    ProgressView("Checking private cloud settings…")
                case .disabled:
                    Label("Cloud AI is off", systemImage: "cloud.slash")
                    Text("Local AI remains the default. Add your own DeepSeek API key to allow task-bound approval proposals.")
                        .font(.callout).foregroundStyle(.secondary)
                    SecureField("DeepSeek API key", text: $deepSeekAPIKey)
                        .textFieldStyle(.roundedBorder)
                        .accessibilityLabel("DeepSeek API key")
                    Button("Save in Keychain and enable") { Task { await saveAndEnableCloud() } }
                        .buttonStyle(.borderedProminent)
                        .disabled(deepSeekAPIKey.isEmpty)
                case .enabled(let model):
                    Label("Cloud AI available with approval", systemImage: "checkmark.shield.fill")
                        .foregroundStyle(.green)
                    Text("DeepSeek credential is stored in this Mac's Keychain. Its value is never displayed.")
                        .font(.callout).foregroundStyle(.secondary)
                    Text("\(model) · every request still requires a separate preview and approval")
                        .font(.callout).foregroundStyle(.secondary)
                    SecureField("Replace DeepSeek API key", text: $deepSeekAPIKey)
                        .textFieldStyle(.roundedBorder)
                        .accessibilityLabel("Replacement DeepSeek API key")
                    Button("Replace credential") { Task { await saveAndEnableCloud() } }
                        .disabled(deepSeekAPIKey.isEmpty)
                    Button("Disable cloud and remove key", role: .destructive) {
                        Task { await disableCloud() }
                    }
                case .saving:
                    ProgressView("Updating Keychain and private routing preference…")
                case .failed(let message):
                    Label("Cloud settings need attention", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                    Button("Check again") { Task { await loadCloudSettings() } }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private var routeBadge: some View {
        Label(runtimeIndicatorTitle, systemImage: runtimeIndicatorIcon)
            .font(.caption.weight(.medium))
            .padding(.horizontal, 10).padding(.vertical, 6)
            .background(runtimeIndicatorColor.opacity(0.12), in: Capsule())
            .foregroundStyle(runtimeIndicatorColor)
    }

    private func taskBubble(_ text: String) -> some View {
        HStack {
            Spacer(minLength: 80)
            Text(text)
                .textSelection(.enabled)
                .padding(.horizontal, 14).padding(.vertical, 10)
                .background(Color.accentColor.opacity(0.12), in: RoundedRectangle(cornerRadius: 14))
        }
    }

    private func resultCard<Content: View>(
        title: String, icon: String, color: Color,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Label(title, systemImage: icon)
                .font(.headline).foregroundStyle(color)
            content()
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(.separator.opacity(0.65)))
    }

    private func metadata(_ route: String, correlation: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(route)
            Text("Audit · \(correlation)").textSelection(.enabled)
        }
        .font(.caption).foregroundStyle(.secondary)
    }

    private var runtimeIndicatorTitle: String {
        switch runtimeState {
        case .running, .sampling, .sample: "Local AI ready"
        case .starting, .loading: "Checking local AI"
        case .stopped: "Local AI stopped"
        case .degraded: "Recovery needed"
        case .failed: "Status unavailable"
        }
    }

    private var runtimeIndicatorIcon: String {
        switch runtimeState {
        case .running, .sampling, .sample: "checkmark.circle.fill"
        case .starting, .loading: "circle.dotted"
        case .stopped: "stop.circle"
        case .degraded: "exclamationmark.triangle.fill"
        case .failed: "xmark.circle.fill"
        }
    }

    private var runtimeIndicatorColor: Color {
        switch runtimeState {
        case .running, .sampling, .sample: .green
        case .starting, .loading: .secondary
        case .stopped: .secondary
        case .degraded: .orange
        case .failed: .red
        }
    }

    private func submitWorkbenchTask() {
        let text = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !taskState.isBusy else { return }
        prompt = ""
        currentTaskPrompt = text
        taskState = .submitting(text)
        Task { await runWorkbenchTask(text) }
    }

    @MainActor
    private func runWorkbenchTask(_ text: String) async {
        guard let context = taskContext() else {
            taskState = .failed("The task router or one of its signed catalogs is missing.")
            return
        }
        taskState = await Task.detached { () -> WorkbenchTaskState in
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                let payload = try SupervisorClient(executableURL: context.supervisor).submitTask(
                    rootURL: context.root,
                    modelCatalogURL: context.models,
                    hardwareProfilesURL: context.hardware,
                    localProfilesURL: context.localProfiles,
                    evidenceRootURL: context.evidenceRoot,
                    cloudCatalogURL: context.cloud,
                    prompt: text,
                    maximumOutputTokens: 64,
                    omlxAPIKey: secrets.omlxAPIKey,
                    brokerToken: secrets.brokerToken,
                    memoryToken: secrets.memoryToken
                )
                switch payload.plan.route {
                case "local":
                    guard let result = payload.result else {
                        return .failed("The local route returned no validated result.")
                    }
                    return .localResult(result.output, result.model, result.correlationID)
                case "cloud_proposal_required":
                    guard let proposal = payload.proposal else {
                        return .failed("The cloud route returned no approval proposal.")
                    }
                    return .cloudProposal(proposal)
                case "capability_unavailable":
                    let code = payload.cloudUnavailableCode ?? payload.plan.reasonCodes.joined(separator: ", ")
                    return .unavailable(userFacingRouteMessage(code))
                default:
                    return .failed("The task router returned an unsupported state.")
                }
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func loadCloudSettings() async {
        guard let context = taskContext() else {
            cloudSetupState = .failed("The cloud provider catalog or Supervisor is missing.")
            return
        }
        cloudSetupState = .loading
        cloudSetupState = await Task.detached { () -> CloudSetupViewState in
            do {
                let credentialExists = try CloudCredentialCoordinator().status()
                let preference = try SupervisorClient(executableURL: context.supervisor)
                    .cloudSettings(rootURL: context.root, catalogURL: context.cloud)
                guard preference.valid else { return .failed("Cloud preference state is invalid and was disabled.") }
                if preference.enabled {
                    guard credentialExists, let model = preference.modelID else {
                        return .failed("Cloud routing is enabled but its Keychain credential is missing.")
                    }
                    return .enabled(model)
                }
                return .disabled
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func saveAndEnableCloud() async {
        guard let context = taskContext() else {
            cloudSetupState = .failed("The cloud provider catalog or Supervisor is missing.")
            return
        }
        let key = deepSeekAPIKey
        deepSeekAPIKey = ""
        cloudSetupState = .saving
        cloudSetupState = await Task.detached { () -> CloudSetupViewState in
            let credentials = CloudCredentialCoordinator()
            do {
                try credentials.saveDeepSeekAPIKey(key)
                let preference = try SupervisorClient(executableURL: context.supervisor).setCloudSettings(
                    rootURL: context.root, catalogURL: context.cloud, enabled: true,
                    modelID: "deepseek-v4-flash"
                )
                guard preference.valid, preference.enabled, let model = preference.modelID else {
                    try? credentials.deleteDeepSeekAPIKey()
                    return .failed("Cloud routing did not persist a valid enabled state.")
                }
                return .enabled(model)
            } catch {
                try? credentials.deleteDeepSeekAPIKey()
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func disableCloud() async {
        guard let context = taskContext() else {
            cloudSetupState = .failed("The cloud provider catalog or Supervisor is missing.")
            return
        }
        cloudSetupState = .saving
        cloudSetupState = await Task.detached { () -> CloudSetupViewState in
            do {
                let preference = try SupervisorClient(executableURL: context.supervisor).setCloudSettings(
                    rootURL: context.root, catalogURL: context.cloud, enabled: false
                )
                guard preference.valid, !preference.enabled else {
                    return .failed("Cloud routing did not persist a disabled state.")
                }
                try CloudCredentialCoordinator().deleteDeepSeekAPIKey()
                return .disabled
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func approveAndExecute(_ proposal: CloudProposalPayload) async {
        guard let context = taskContext() else {
            taskState = .failed("The cloud execution context is missing.")
            return
        }
        taskState = .cloudExecuting
        taskState = await Task.detached { () -> WorkbenchTaskState in
            do {
                guard let key = try CloudCredentialCoordinator().readDeepSeekAPIKey() else {
                    return .unavailable("Cloud approval requires a user-provided API key in Settings & Recovery.")
                }
                let client = try SupervisorClient(executableURL: context.supervisor)
                _ = try client.approveCloud(
                    rootURL: context.root, proposalID: proposal.proposalID,
                    maximumCostUSD: proposal.estimatedCost.maximum
                )
                let execution = try client.executeCloud(
                    rootURL: context.root, catalogURL: context.cloud,
                    proposalID: proposal.proposalID, deepSeekAPIKey: key
                )
                return .cloudResult(
                    execution.result.content, execution.result.model,
                    execution.result.usage.costUSD, proposal.correlationID
                )
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func rejectProposal(_ proposal: CloudProposalPayload) async {
        guard let context = taskContext() else {
            taskState = .failed("The cloud proposal context is missing.")
            return
        }
        taskState = await Task.detached { () -> WorkbenchTaskState in
            do {
                let decision = try SupervisorClient(executableURL: context.supervisor)
                    .rejectCloud(rootURL: context.root, proposalID: proposal.proposalID)
                return decision.outcome == "denied"
                    ? .denied : .failed("The proposal was not rejected cleanly.")
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    private func taskContext() -> TaskContext? {
        guard let installation = installationContext(),
              let models = bundledOrDevelopment("models", extension: "json", development: "config/models.json"),
              let hardware = bundledOrDevelopment("hardware-profiles", extension: "json", development: "config/hardware-profiles.yaml"),
              let local = bundledOrDevelopment("local-model-profiles", extension: "json", development: "config/local-model-profiles.json"),
              let cloud = bundledOrDevelopment("cloud-providers", extension: "json", development: "config/cloud-providers.json")
        else { return nil }
        let evidenceRoot = Bundle.main.resourceURL ?? URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        return TaskContext(
            supervisor: installation.supervisor, root: installation.root, models: models,
            hardware: hardware, localProfiles: local, cloud: cloud, evidenceRoot: evidenceRoot
        )
    }

    private func bundledOrDevelopment(_ name: String, extension suffix: String, development: String) -> URL? {
        if let bundled = Bundle.main.url(forResource: name, withExtension: suffix) { return bundled }
        let url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent(development)
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    nonisolated private func userFacingRouteMessage(_ code: String) -> String {
        switch code {
        case "CLOUD_DATA_CLASS_BLOCKED": "This task contains data that is not allowed to leave the Mac. Remove credentials or sensitive third-party data and try again."
        case "CLOUD_PRICING_STALE": "Current cloud pricing cannot be verified, so the task was not sent. Refresh the provider catalog in Settings."
        case "local_unhealthy": "Local AI is not ready and cloud use is disabled. Open recovery settings to start or repair it."
        default: "The verified local route cannot handle this task, and no safe cloud route is currently available."
        }
    }

    @ViewBuilder
    private var runtimeSection: some View {
        GroupBox("Local AI runtime") {
            VStack(alignment: .leading, spacing: 8) {
                switch runtimeState {
                case .loading:
                    ProgressView("Reading managed runtime state…")
                case .stopped:
                    Label("Local runtime is stopped", systemImage: "stop.circle")
                    Button("Start local AI") { Task { await startRuntime() } }
                        .buttonStyle(.borderedProminent)
                case .starting:
                    ProgressView("Starting oMLX, loading the model, and verifying the Broker…")
                case .running:
                    Label("Local runtime and policy Broker are running", systemImage: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    HStack {
                        Button("Run verified sample task") { Task { await runSampleTask() } }
                            .buttonStyle(.borderedProminent)
                        Button("Stop local AI") { Task { await stopRuntime() } }
                    }
                case .sampling:
                    ProgressView("Running a local sample task through the audited Broker…")
                case .sample(let model, let output, let correlation):
                    Label("Verified local sample completed", systemImage: "checkmark.seal.fill")
                        .foregroundStyle(.green)
                    Text("Model: \(model)")
                    Text(output).font(.headline).textSelection(.enabled)
                    Text("Audit correlation: \(correlation)")
                        .font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                    HStack {
                        Button("Run again") { Task { await runSampleTask() } }
                        Button("Stop local AI") { Task { await stopRuntime() } }
                    }
                case .degraded(let message):
                    Label("Runtime needs recovery", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text(message).font(.callout).foregroundStyle(.secondary)
                    Button("Stop managed processes safely") { Task { await stopRuntime() } }
                case .failed(let message):
                    Label("Runtime action failed safely", systemImage: "xmark.octagon.fill")
                        .foregroundStyle(.red)
                    Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                    Button("Refresh status") { Task { await loadRuntimeStatus() } }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private var modelSection: some View {
        GroupBox("Local model") {
            VStack(alignment: .leading, spacing: 8) {
                switch modelState {
                case .loading:
                    ProgressView("Verifying existing model cache…")
                case .unavailable(let message):
                    Label("No verified reusable model", systemImage: "externaldrive.badge.questionmark")
                        .foregroundStyle(.orange)
                    Text(message).font(.callout).foregroundStyle(.secondary)
                case .planned(let plan):
                    Label("Verified existing \(plan.repository)", systemImage: "checkmark.seal.fill")
                        .foregroundStyle(.green)
                    Text("Reuse \(byteCount(plan.sizeBytes)) without downloading or copying model weights.")
                    Text("License: \(plan.license) · \(precision(plan)) · revision \(plan.revision.prefix(12))")
                        .font(.caption).foregroundStyle(.secondary)
                    Text("Verified capabilities: \(plan.capabilities.joined(separator: ", "))")
                        .font(.caption).foregroundStyle(.secondary)
                    if !plan.capabilities.contains("embedding") {
                        Label(
                            "Semantic memory search is unavailable until a separately verified embedding model is approved.",
                            systemImage: "exclamationmark.triangle.fill"
                        )
                        .foregroundStyle(.orange)
                        .font(.callout)
                    }
                    Text("The source cache remains externally owned and will not be deleted by this product.")
                        .font(.caption).foregroundStyle(.secondary)
                    Button("Approve existing model reference") {
                        Task { await linkModel(plan) }
                    }
                    .buttonStyle(.borderedProminent)
                case .linking:
                    ProgressView("Creating verified zero-copy model reference…")
                case .linked(let path):
                    Label("Existing model linked without copying", systemImage: "link.circle.fill")
                        .foregroundStyle(.green)
                    Text(path).font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                case .failed(let message):
                    Label("Model reference failed safely", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.red)
                    Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                    Button("Verify again") { Task { await loadModelPlan() } }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private var embeddingSection: some View {
        GroupBox("Semantic memory model") {
            VStack(alignment: .leading, spacing: 8) {
                switch embeddingState {
                case .loading:
                    ProgressView("Checking the pinned multilingual embedding model…")
                case .planned(let plan):
                    Label(
                        plan.availableVerified ? "Verified model is ready to reuse" : "Embedding model is not downloaded",
                        systemImage: plan.availableVerified ? "checkmark.seal.fill" : "arrow.down.circle"
                    )
                    .foregroundStyle(plan.availableVerified ? .green : .orange)
                    Text("\(plan.repository) · \(byteCount(plan.sizeBytes)) · \(plan.license)")
                    Text("Pinned revision \(plan.revision.prefix(12)) · \(plan.embeddingDimension ?? 0)-dimension vectors")
                        .font(.caption).foregroundStyle(.secondary)
                    if plan.availableVerified {
                        Text("Approval creates a zero-copy reference and enables governed semantic search. The runtime must be stopped.")
                            .font(.callout).foregroundStyle(.secondary)
                        Button("Approve and activate semantic memory model") {
                            Task { await activateEmbedding(plan) }
                        }
                        .buttonStyle(.borderedProminent)
                    } else {
                        Text("No download has started. Approval downloads only this pinned revision, resumes interruptions, and verifies every file before use.")
                            .font(.callout).foregroundStyle(.secondary)
                        Button("Approve and download \(byteCount(plan.sizeBytes))") {
                            Task { await downloadEmbedding(plan) }
                        }
                        .buttonStyle(.borderedProminent)
                    }
                case .downloading(let size):
                    ProgressView("Downloading and verifying \(byteCount(size))…")
                case .activating:
                    ProgressView("Verifying files and activating semantic memory safely…")
                case .active(let model, let dimension):
                    Label("Semantic memory model active", systemImage: "brain.head.profile.fill")
                        .foregroundStyle(.green)
                    Text("\(model) · \(dimension)-dimension vectors")
                case .failed(let message):
                    Label("Semantic memory activation failed safely", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.red)
                    Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                    Button("Check again") { Task { await loadEmbeddingPlan() } }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
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
                    if plan.cachedArtifactVerified {
                        Text("Verified installer cached · no download required")
                    } else {
                        Text("Download: \(byteCount(plan.artifactSizeBytes - plan.downloadedBytes)) remaining of \(byteCount(plan.artifactSizeBytes))")
                    }
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
        let explicitPath = ManifestArgumentResolver.explicitManifestPath(in: CommandLine.arguments)
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
                    ports: [8000, 43110, 43111]
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
                if let blocker = plan.cacheBlocker {
                    return .unavailable("Cached installer requires repair: \(blocker).")
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

    @MainActor
    private func loadModelPlan() async {
        guard let context = modelContext() else {
            modelState = .unavailable("The pinned model catalog or standard Hugging Face cache is missing.")
            return
        }
        modelState = .loading
        modelState = await Task.detached { () -> ModelViewState in
            do {
                let client = try SupervisorClient(executableURL: context.supervisor)
                let plan = try client.modelPlan(
                    rootURL: context.root,
                    cacheRootURL: context.cacheRoot,
                    catalogURL: context.catalog
                )
                guard plan.schemaVersion == 1, plan.approvalRequired,
                      plan.revision.count == 40, plan.sizeBytes > 0 else {
                    return .failed("Supervisor returned an invalid model plan.")
                }
                if !plan.availableVerified {
                    return .unavailable("Pinned model is not reusable: \(plan.unavailableReason ?? "unknown reason").")
                }
                return .planned(plan)
            } catch {
                return .unavailable(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func linkModel(_ plan: ModelPlanPayload) async {
        guard let context = modelContext() else {
            modelState = .failed("The model context is no longer available.")
            return
        }
        modelState = .linking
        modelState = await Task.detached { () -> ModelViewState in
            do {
                let client = try SupervisorClient(executableURL: context.supervisor)
                let linked = try client.linkModel(
                    rootURL: context.root,
                    cacheRootURL: context.cacheRoot,
                    catalogURL: context.catalog,
                    approvedRevision: plan.revision
                )
                guard linked.schemaVersion == 1,
                      linked.reference.revision == plan.revision,
                      linked.reference.storageMode == "external-reference",
                      linked.reference.sourceOwnership == "external-cache-not-product-owned" else {
                    return .failed("Supervisor returned an invalid model reference.")
                }
                return .linked(linked.reference.linkPath)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func loadEmbeddingPlan() async {
        guard let context = modelContext() else {
            embeddingState = .failed("The pinned model catalog or standard Hugging Face cache is missing.")
            return
        }
        embeddingState = .loading
        embeddingState = await Task.detached { () -> EmbeddingViewState in
            do {
                let plan = try SupervisorClient(executableURL: context.supervisor).embeddingPlan(
                    rootURL: context.root,
                    cacheRootURL: context.cacheRoot,
                    catalogURL: context.catalog
                )
                guard plan.schemaVersion == 1, plan.approvalRequired,
                      plan.revision.count == 40, plan.sizeBytes > 0,
                      plan.capabilities.contains("embedding"),
                      (plan.embeddingDimension ?? 0) > 0 else {
                    return .failed("Supervisor returned an invalid embedding model plan.")
                }
                return .planned(plan)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func activateEmbedding(_ plan: ModelPlanPayload) async {
        guard let context = modelContext() else {
            embeddingState = .failed("The embedding model context is no longer available.")
            return
        }
        embeddingState = .activating
        embeddingState = await Task.detached { () -> EmbeddingViewState in
            do {
                let activated = try SupervisorClient(executableURL: context.supervisor).activateEmbedding(
                    rootURL: context.root,
                    cacheRootURL: context.cacheRoot,
                    catalogURL: context.catalog,
                    approvedRevision: plan.revision
                )
                guard activated.schemaVersion == 1,
                      activated.route.revision == plan.revision,
                      activated.route.expectedDimension == plan.embeddingDimension,
                      activated.reference.storageMode == "external-reference" else {
                    return .failed("Supervisor returned an invalid embedding activation result.")
                }
                return .active(activated.route.apiModel, activated.route.expectedDimension)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func downloadEmbedding(_ plan: ModelPlanPayload) async {
        guard let context = modelContext() else {
            embeddingState = .failed("The embedding model context is no longer available.")
            return
        }
        embeddingState = .downloading(plan.sizeBytes)
        embeddingState = await Task.detached { () -> EmbeddingViewState in
            do {
                let downloaded = try SupervisorClient(executableURL: context.supervisor).downloadEmbedding(
                    rootURL: context.root,
                    cacheRootURL: context.cacheRoot,
                    catalogURL: context.catalog,
                    approvedRevision: plan.revision
                )
                guard downloaded.schemaVersion == 1,
                      downloaded.modelID == plan.modelID,
                      downloaded.revision == plan.revision,
                      downloaded.totalSizeBytes == plan.sizeBytes else {
                    return .failed("Supervisor returned an invalid embedding download result.")
                }
                let refreshed = try SupervisorClient(executableURL: context.supervisor).embeddingPlan(
                    rootURL: context.root,
                    cacheRootURL: context.cacheRoot,
                    catalogURL: context.catalog
                )
                guard refreshed.availableVerified else {
                    return .failed("Downloaded files did not pass the final model verification.")
                }
                return .planned(refreshed)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func loadRuntimeStatus() async {
        guard let context = installationContext() else {
            runtimeState = .failed("Supervisor context is unavailable.")
            return
        }
        runtimeState = .loading
        runtimeState = await Task.detached { () -> RuntimeViewState in
            do {
                let status = try SupervisorClient(executableURL: context.supervisor)
                    .runtimeStatus(rootURL: context.root)
                guard status.schemaVersion == 1 else { return .failed("Unsupported runtime status.") }
                switch status.phase {
                case "stopped": return .stopped
                case "running" where status.omlxAlive && status.brokerAlive: return .running
                default: return .degraded("Recorded phase: \(status.phase). oMLX: \(status.omlxAlive), Broker: \(status.brokerAlive).")
                }
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func startRuntime() async {
        guard let context = installationContext() else {
            runtimeState = .failed("Supervisor context is unavailable.")
            return
        }
        runtimeState = .starting
        runtimeState = await Task.detached { () -> RuntimeViewState in
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                let result = try SupervisorClient(executableURL: context.supervisor).startRuntime(
                    rootURL: context.root,
                    omlxAPIKey: secrets.omlxAPIKey,
                    brokerToken: secrets.brokerToken,
                    memoryToken: secrets.memoryToken
                )
                return result.runtime.phase == "running" ? .running : .degraded("Runtime did not reach running state.")
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func stopRuntime() async {
        guard let context = installationContext() else {
            runtimeState = .failed("Supervisor context is unavailable.")
            return
        }
        runtimeState = .loading
        runtimeState = await Task.detached { () -> RuntimeViewState in
            do {
                let result = try SupervisorClient(executableURL: context.supervisor)
                    .stopRuntime(rootURL: context.root)
                return result.runtime.phase == "stopped" ? .stopped : .failed("Runtime did not stop.")
            } catch {
                return .failed(String(describing: error))
            }
        }.value
    }

    @MainActor
    private func runSampleTask() async {
        guard let context = installationContext() else {
            runtimeState = .failed("Supervisor context is unavailable.")
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
                    return .failed("Sample result was empty or unsupported.")
                }
                return .sample(sample.model, sample.output, sample.correlationID)
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
            root: support.appendingPathComponent("Forma AI", isDirectory: true)
        )
    }

    private func modelContext() -> ModelContext? {
        guard let installation = installationContext(),
              let catalog = Bundle.main.url(forResource: "models", withExtension: "json")
                ?? developmentModelsURL()
        else { return nil }
        let cache = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".cache/huggingface/hub", isDirectory: true)
        guard FileManager.default.fileExists(atPath: cache.path) else { return nil }
        return ModelContext(
            supervisor: installation.supervisor,
            root: installation.root,
            cacheRoot: cache,
            catalog: catalog
        )
    }

    private func developmentUpstreamsURL() -> URL? {
        let url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
            .appendingPathComponent("config/upstreams.json")
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    private func developmentModelsURL() -> URL? {
        let url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
            .appendingPathComponent("config/models.json")
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    private func byteCount(_ count: Int64) -> String {
        ByteCountFormatter.string(fromByteCount: max(0, count), countStyle: .file)
    }

    private func precision(_ plan: ModelPlanPayload) -> String {
        plan.quantizationBits.map { "\($0)-bit" } ?? "unquantized MLX"
    }

    private func supervisorExecutableURL() -> URL? {
        let bundled = Bundle.main.bundleURL
            .appendingPathComponent("Contents/Helpers/Supervisor", isDirectory: true)
            .appendingPathComponent("forma-ai-supervisor", isDirectory: false)
        if FileManager.default.isExecutableFile(atPath: bundled.path) {
            return bundled
        }
        guard let path = ProcessInfo.processInfo.environment["FORMA_AI_SUPERVISOR"],
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

private struct ModelContext: Sendable {
    let supervisor: URL
    let root: URL
    let cacheRoot: URL
    let catalog: URL
}

private enum InstallationViewState: Sendable {
    case loading
    case unavailable(String)
    case planned(InstallationPlanPayload)
    case installing(String)
    case installed(String)
    case failed(String)
}

private enum ModelViewState: Sendable {
    case loading
    case unavailable(String)
    case planned(ModelPlanPayload)
    case linking
    case linked(String)
    case failed(String)
}

private enum EmbeddingViewState: Sendable {
    case loading
    case planned(ModelPlanPayload)
    case downloading(Int64)
    case activating
    case active(String, Int)
    case failed(String)
}

private enum RuntimeViewState: Sendable {
    case loading
    case stopped
    case starting
    case running
    case sampling
    case sample(String, String, String)
    case degraded(String)
    case failed(String)
}

private enum WorkspaceSection: String, Hashable {
    case newTask
    case history
    case settings

    init(_ destination: WorkbenchDestination) {
        switch destination {
        case .newTask: self = .newTask
        case .history: self = .history
        case .settings: self = .settings
        }
    }
}

private extension ModelRouteChoice {
    var title: String {
        switch self {
        case .automaticLocalFirst: "Automatic · local first"
        case .localOnly: "Local only"
        case .cloudWithApproval: "Cloud · ask every time"
        }
    }

    var isExecutionBound: Bool {
        self == .automaticLocalFirst
    }

    var bindingStatus: String {
        switch self {
        case .automaticLocalFirst: "Ready"
        case .localOnly, .cloudWithApproval: "Execution binding pending"
        }
    }

    var safetyDescription: String {
        switch self {
        case .automaticLocalFirst:
            "Local by default. A cloud proposal never sends data until you approve the exact request."
        case .localOnly:
            "Local-only preference is saved for this task, but submission waits until the Supervisor routing contract accepts it."
        case .cloudWithApproval:
            "Cloud preference never authorizes sending. A credential, exact payload preview, and separate approval are still required; submission waits for routing-contract support."
        }
    }
}

private enum WorkbenchTaskState: Sendable {
    case idle
    case submitting(String)
    case localResult(String, String, String)
    case cloudProposal(CloudProposalPayload)
    case cloudExecuting
    case cloudResult(String, String, Double, String)
    case denied
    case unavailable(String)
    case failed(String)

    var isBusy: Bool {
        if case .submitting = self { return true }
        return false
    }
}

private enum CloudSetupViewState: Sendable {
    case loading
    case disabled
    case enabled(String)
    case saving
    case failed(String)
}

private struct TaskContext: Sendable {
    let supervisor: URL
    let root: URL
    let models: URL
    let hardware: URL
    let localProfiles: URL
    let cloud: URL
    let evidenceRoot: URL
}
