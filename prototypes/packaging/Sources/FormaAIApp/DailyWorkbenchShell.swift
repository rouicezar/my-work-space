import SwiftUI
import LifecycleContract
import SupervisorProtocol
import RuntimeSecurity

enum DailyWorkbenchPresentation: Sendable {
    case preview
    case production
}

struct DailyWorkbenchShell: View {
    let presentation: DailyWorkbenchPresentation

    private let contract = DailyWorkbenchSurfaceContract.productDefault
    @State private var language: ProductLanguage = OnboardingPreferences.storedLanguage
    @AppStorage(OnboardingPreferences.sidebarWidthKey) private var sidebarWidth: Double = 230
    @AppStorage(OnboardingPreferences.supervisionWidthKey) private var trailingWidth: Double = 270
    @State private var prompt = ""
    @State private var route: PreviewComposerRoute = .localFirst
    @State private var supervisionExpanded = true
    @State private var contextPreviewPresented = false
    @State private var transitionStage: PreviewTransitionStage = .compose
    @State private var destination: DailyWorkbenchDestination = .newTask
    @State private var historySelection: HistoryPreviewTaskState = .interrupted
    @State private var memorySelection: GovernedMemoryReviewState = .candidate
    @State private var settingsSection: DailyWorkbenchSettingsSection = .memory
    @State private var agentSelection: AgentAdapterKind = .herdrTerminal
    @State private var permissionSelection: PermissionScope = .write
    @State private var modelRouteSelection: ModelRouteState = .automaticLocalFirst
    @State private var runtimeSelection: RuntimeFinalState = .stopped

    @State private var selectedModelChoice: ModelRouteChoice = WorkbenchSurfaceContract.productDefault.modelSelection.defaultChoice
    @State private var currentTaskPrompt = ""
    @State private var taskState: WorkbenchTaskState = .idle
    @State private var agentActivityState: AgentActivityViewState = .loading
    @State private var cloudSetupState: CloudSetupViewState = .loading
    @State private var deepSeekAPIKey = ""
    @State private var result: Result<ProductManifest, Error>?
    @State private var supervisorState: SupervisorViewState = .loading
    @State private var installationState: InstallationViewState = .loading
    @State private var modelState: ModelViewState = .loading
    @State private var embeddingState: EmbeddingViewState = .loading
    @State private var runtimeState: RuntimeViewState = .loading

#if DEBUG
    private let agentActivityFixture: RuntimePresentationState?

    init(presentation: DailyWorkbenchPresentation) {
        self.presentation = presentation
        self.agentActivityFixture = nil
    }

    init(presentation: DailyWorkbenchPresentation, agentActivityFixture: RuntimePresentationState) {
        self.presentation = presentation
        self.agentActivityFixture = agentActivityFixture
        _agentActivityState = State(initialValue: .ready(agentActivityFixture))
    }
#else
    init(presentation: DailyWorkbenchPresentation) {
        self.presentation = presentation
    }
#endif


    var body: some View {
        let copy = ProductCopy(language: language)

        VStack(spacing: 0) {
            Group {
                if presentation == .preview {
                    previewDisclosure(copy)
                } else {
                    productionChrome(copy)
                }
            }
            ResizableWorkbenchLayout(
                sidebarWidth: Binding(get: { CGFloat(sidebarWidth) }, set: { sidebarWidth = Double($0) }),
                trailingWidth: Binding(get: { CGFloat(trailingWidth) }, set: { trailingWidth = Double($0) }),
                trailingVisible: supervisionExpanded,
                sidebar: { sidebar(copy) },
                content: { mainContent(copy) },
                trailing: {
                    supervisionRail(copy)
                        .transition(.move(edge: .trailing).combined(with: .opacity))
                }
            )
        }
        .frame(minWidth: 900, minHeight: 620)
        .animation(.easeInOut(duration: 0.18), value: supervisionExpanded)
        .task {
            guard presentation == .production else { return }
            await loadRuntimeStatus()
            await loadAgentActivity()
            await loadCloudSettings()
        }
        .alert(copy[.contextPreviewTitle], isPresented: $contextPreviewPresented) {
            Button(copy[.dismiss], role: .cancel) {}
        } message: {
            Text(copy[.contextPreviewBody])
        }
    }

    @ViewBuilder
    private func mainContent(_ copy: ProductCopy) -> some View {
        if destination == .settings {
            settingsSurface(copy)
        } else if destination == .history {
            if presentation == .production, let context = installationContext() {
                HistoryRecoveryPanel(language: language, supervisorURL: context.supervisor, rootURL: context.root)
            } else {
                HistoryRecoveryPreview(language: language, selection: $historySelection)
            }
        } else if presentation == .production {
            if case .idle = taskState {
                DailyWorkbenchComposerSurface(
                    language: language,
                    prompt: $prompt,
                    modelChoices: WorkbenchSurfaceContract.productDefault.modelSelection.availableChoices,
                    selectedModelChoice: $selectedModelChoice,
                    isActionDisabled: taskState.isBusy || !selectedModelChoice.isExecutionBound,
                    onAction: submitWorkbenchTask
                )
            } else {
                taskExecutionSurface(copy)
            }
        } else if transitionStage == .compose {
            DailyWorkbenchComposerSurface(
                language: language,
                prompt: $prompt,
                previewRoute: $route,
                isActionDisabled: prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                onAction: { transitionStage = .routeReview },
                onPreviewContext: { contextPreviewPresented = true }
            )
        } else {
            ExecutionJourneyPreview(
                language: language,
                stage: transitionStage,
                goal: prompt,
                onAdvance: advanceTransition,
                onBackToEdit: { transitionStage = .compose }
            )
        }
    }

    @ViewBuilder
    private func settingsSurface(_ copy: ProductCopy) -> some View {
        HStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 6) {
                settingsSectionRow(.memory, copy[.memoryTitle], "brain.head.profile")
                settingsSectionRow(.agentsTools, copy[.agentsToolsTitle], "rectangle.3.group")
                settingsSectionRow(.permissions, copy[.permissionsTitle], "hand.raised")
                settingsSectionRow(.modelsProviders, copy[.modelsProvidersTitle], "cpu")
                settingsSectionRow(.localRuntime, copy[.localRuntimeTitle], "gearshape.2")
                settingsSectionRow(.dataPrivacy, copy[.dataPrivacyTitle], "lock.shield")
                settingsSectionRow(.diagnostics, copy[.diagnosticsTitle], "wrench.and.screwdriver")
                Spacer()
            }
            .padding(16).frame(width: 170).background(.thinMaterial)
            Divider()
            settingsSectionContent(copy)
        }
    }

    private func settingsSectionRow(_ section: DailyWorkbenchSettingsSection, _ title: String, _ symbol: String) -> some View {
        let selected = section == settingsSection
        return Button {
            settingsSection = section
        } label: {
            HStack(spacing: 9) {
                Image(systemName: symbol).frame(width: 18)
                Text(title).font(.callout.weight(selected ? .semibold : .regular))
                Spacer()
            }
            .contentShape(Rectangle())
        }
        .padding(.horizontal, 10).padding(.vertical, 8)
        .foregroundStyle(selected ? Color.white : Color.primary)
        .background(selected ? Color.blue : Color.clear, in: RoundedRectangle(cornerRadius: 9))
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func settingsSectionContent(_ copy: ProductCopy) -> some View {
        switch settingsSection {
        case .memory:
            if presentation == .production, let context = installationContext() {
                GovernedMemoryReviewPanel(language: language, supervisorURL: context.supervisor, rootURL: context.root)
            } else {
                GovernedMemoryReviewPreview(language: language, selection: $memorySelection)
            }
        case .agentsTools:
            AgentsToolsPreview(language: language, selection: $agentSelection)
        case .permissions:
            PermissionsPreview(language: language, selection: $permissionSelection)
        case .modelsProviders:
            if presentation == .production {
                VStack(alignment: .leading, spacing: 16) {
                    cloudSettingsSection(copy)
                    ModelsProvidersControlPanel(language: language)
                }
            } else {
                ModelsProvidersPreview(language: language, selection: $modelRouteSelection)
            }
        case .localRuntime:
            if presentation == .production {
                LocalRuntimeControlPanel(language: language)
            } else {
                LocalRuntimePreview(language: language, selection: $runtimeSelection)
            }
        case .dataPrivacy:
            DataPrivacyPreview(language: language)
        case .diagnostics:
            if presentation == .production {
                DiagnosticsRecoveryControlPanel(language: language)
            } else {
                DiagnosticsRecoveryPreview(language: language)
            }
        }
    }

    private func previewDisclosure(_ copy: ProductCopy) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "eye.trianglebadge.exclamationmark")
            Text(copy[.previewNotice]).font(.callout.weight(.semibold))
            Spacer()
            if !supervisionExpanded {
                Button { supervisionExpanded = true } label: {
                    Label(copy[.expandSupervision], systemImage: "sidebar.trailing")
                }
                .buttonStyle(.borderless)
            }
            Menu {
                Button(copy[.simplifiedChinese]) { language = .simplifiedChinese }
                Button(copy[.english]) { language = .english }
            } label: {
                Label(copy[.languageControl], systemImage: "globe")
            }
            .menuStyle(.borderlessButton)
            .fixedSize()
        }
        .padding(.horizontal, 18).padding(.vertical, 9)
        .background(Color(red: 0.96, green: 0.76, blue: 0.22))
        .foregroundStyle(.black.opacity(0.8))
    }

    private func sidebar(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 24) {
            HStack(spacing: 10) {
                Image(systemName: "sparkles.rectangle.stack.fill")
                    .font(.title2).foregroundStyle(.blue)
                Text("Forma AI").font(.headline)
            }

            VStack(alignment: .leading, spacing: 6) {
                navigationRow(copy[.newTask], "square.and.pencil", destination: .newTask)
                navigationRow(copy[.history], "clock.arrow.circlepath", destination: .history)
                navigationRow(copy[.settings], "gearshape", destination: .settings)
            }

            VStack(alignment: .leading, spacing: 10) {
                Text(copy[.recentTasks].uppercased())
                    .font(.caption2.monospaced().weight(.bold)).foregroundStyle(.secondary)
                Text(copy[.noRealHistory]).font(.caption).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                VStack(alignment: .leading, spacing: 7) {
                    HStack {
                        Text(copy[.sampleBadge]).font(.caption2.monospaced().weight(.bold)).foregroundStyle(.blue)
                        Spacer()
                        Image(systemName: "doc.text.magnifyingglass").foregroundStyle(.secondary)
                    }
                    Text(copy[.sampleTask]).font(.callout.weight(.medium))
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(12)
                .background(Color.secondary.opacity(0.08), in: RoundedRectangle(cornerRadius: 12))
            }
            Spacer()
        }
        .padding(22).frame(maxWidth: .infinity, maxHeight: .infinity).background(.thinMaterial)
    }

    private func navigationRow(_ title: String, _ symbol: String, destination target: DailyWorkbenchDestination?) -> some View {
        let selected = target == destination
        return Button {
            if let target { destination = target }
        } label: {
            HStack(spacing: 10) {
                Image(systemName: symbol).frame(width: 18)
                Text(title).font(.callout.weight(selected ? .semibold : .regular))
                Spacer()
            }
            .contentShape(Rectangle())
        }
        .padding(.horizontal, 11).padding(.vertical, 9)
        .foregroundStyle(selected ? Color.white : Color.primary)
        .background(selected ? Color.blue : Color.clear, in: RoundedRectangle(cornerRadius: 10))
        .buttonStyle(.plain)
        .disabled(target == nil)
    }

    private func supervisionRail(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack {
                Text(copy[.supervision]).font(.headline)
                Spacer()
                Button { supervisionExpanded = false } label: {
                    Image(systemName: "sidebar.trailing")
                }
                .buttonStyle(.plain).help(copy[.collapseSupervision])
            }
            VStack(alignment: .leading, spacing: 8) {
                Image(systemName: destination == .settings ? settingsSectionSymbol : (destination == .history ? "clock.arrow.circlepath" : (transitionStage == .compose ? "pause.circle" : "play.circle.fill")))
                    .font(.title).foregroundStyle(destination == .settings || destination == .history || transitionStage != .compose ? Color.blue : Color.secondary)
                Text(destination == .settings ? settingsSectionTitle : (destination == .history ? copy.stateTitle(historySelection) : (transitionStage == .compose ? copy[.noActiveTask] : copy.stageTitle(transitionStage)))).font(.headline)
                Text(destination == .settings ? settingsSectionSummary : (destination == .history ? copy[.truthBoundaryBody] : (transitionStage == .compose ? copy[.supervisionExplanation] : copy[.previewStateNotice])))
                    .font(.caption).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.vertical, 8)
            Divider()
            statusRow(
                copy[.agentStatus],
                destination == .settings ? settingsSectionStatus : (destination == .history ? copy.agentSummary(historySelection) : (transitionStage == .compose ? copy[.waitingForTask] : copy.stageTitle(transitionStage))),
                "person.2"
            )
            statusRow(
                copy[.evidenceStatus],
                destination == .history ? copy.lastVerified(historySelection) : (transitionStage == .validation || transitionStage == .result ? copy[.valid] : copy[.nothingProduced]),
                "checkmark.seal"
            )
            if presentation == .production {
                productionAgentActivity(copy)
            }
            Spacer()
        }
        .padding(20).frame(maxWidth: .infinity, maxHeight: .infinity).background(.ultraThinMaterial)
    }

    private func statusRow(_ title: String, _ value: String, _ symbol: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: symbol).foregroundStyle(.secondary).frame(width: 18)
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.caption.weight(.semibold))
                Text(value).font(.caption).foregroundStyle(.secondary)
            }
        }
    }

    private var settingsSectionSymbol: String {
        switch settingsSection {
        case .memory: "brain.head.profile"
        case .agentsTools: "rectangle.3.group"
        case .permissions: "hand.raised"
        case .modelsProviders: "cpu"
        case .localRuntime: "gearshape.2"
        case .dataPrivacy: "lock.shield"
        case .diagnostics: "wrench.and.screwdriver"
        }
    }

    private var settingsSectionTitle: String {
        let copy = ProductCopy(language: language)
        switch settingsSection {
        case .memory: return copy.memoryStateTitle(memorySelection)
        case .agentsTools: return copy.agentKindTitle(agentSelection)
        case .permissions: return copy.permissionScopeTitle(permissionSelection)
        case .modelsProviders: return copy.modelRouteTitle(modelRouteSelection)
        case .localRuntime: return copy.runtimeStateTitle(runtimeSelection)
        case .dataPrivacy: return copy[.dataPrivacyTitle]
        case .diagnostics: return copy[.diagnosticsTitle]
        }
    }

    private var settingsSectionSummary: String {
        let copy = ProductCopy(language: language)
        switch settingsSection {
        case .memory: return copy[.memorySyntheticOnly]
        case .agentsTools: return copy[.agentsToolsSyntheticOnly]
        case .permissions: return copy[.permissionsSyntheticOnly]
        case .modelsProviders: return copy[.modelsProvidersSyntheticOnly]
        case .localRuntime: return copy[.localRuntimeSyntheticOnly]
        case .dataPrivacy: return copy[.dataPrivacySyntheticOnly]
        case .diagnostics: return copy[.diagnosticsSyntheticOnly]
        }
    }

    private var settingsSectionStatus: String {
        let copy = ProductCopy(language: language)
        switch settingsSection {
        case .memory: return copy.memoryProvenance(memorySelection)
        case .agentsTools: return copy.agentKindDetail(agentSelection)
        case .permissions: return copy.permissionScopeDetail(permissionSelection)
        case .modelsProviders: return copy.modelRouteDetail(modelRouteSelection)
        case .localRuntime: return copy.runtimeStateDetail(runtimeSelection)
        case .dataPrivacy: return copy[.dataPrivacyBoundaryBody]
        case .diagnostics: return copy[.diagnosticsBoundaryBody]
        }
    }

    private func advanceTransition() {
        let stages = ComposeToExecutionPreviewContract.productDefault.stages
        guard let index = stages.firstIndex(of: transitionStage), index + 1 < stages.count else { return }
        transitionStage = stages[index + 1]
    }

    private func productionChrome(_ copy: ProductCopy) -> some View {
        HStack(spacing: 10) {
            HStack(spacing: 8) {
                Circle().fill(runtimeIndicatorColor).frame(width: 8, height: 8)
                Text(runtimeIndicatorTitle(copy))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if !supervisionExpanded {
                Button { supervisionExpanded = true } label: {
                    Label(copy[.expandSupervision], systemImage: "sidebar.trailing")
                }
                .buttonStyle(.borderless)
            }
            Menu {
                Button(copy[.simplifiedChinese]) { language = .simplifiedChinese }
                Button(copy[.english]) { language = .english }
            } label: {
                Label(copy[.languageControl], systemImage: "globe")
            }
            .menuStyle(.borderlessButton)
            .fixedSize()
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 9)
        .background(.bar)
    }

    private func taskExecutionSurface(_ copy: ProductCopy) -> some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(copy[.newTask]).font(.title2.weight(.semibold))
                    Text(copy.taskPrivacySubtitle)
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                routeBadge(copy)
                Button(copy.taskNewTaskButton) { resetWorkbenchTask() }
                    .buttonStyle(.bordered)
            }
            .padding(.horizontal, 28).padding(.vertical, 18)
            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    switch taskState {
                    case .idle:
                        EmptyView()
                    case .submitting(let text):
                        taskBubble(text)
                        HStack(spacing: 10) {
                            ProgressView()
                            Text(copy.runtimeCheckingRoute)
                                .foregroundStyle(.secondary)
                        }
                    case .accepted(let model, let correlation):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: copy.taskAccepted, icon: "clock", color: .blue) {
                            Text(copy.taskAcceptedHistoryHint)
                            metadata(copy.localModelRoute(model), correlation: correlation, copy: copy)
                            Button(copy[.history]) { destination = .history }
                        }
                    case .localResult(let text, let model, let correlation):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: copy.taskCompletedLocal, icon: "checkmark.circle.fill", color: .green) {
                            Text(text).textSelection(.enabled)
                            metadata(copy.localModelRoute(model), correlation: correlation, copy: copy)
                        }
                    case .cloudProposal(let proposal):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: copy.taskApprovalRequired, icon: "lock.shield.fill", color: .orange) {
                            Text(copy.taskCloudBoundary)
                            Grid(alignment: .leading, horizontalSpacing: 18, verticalSpacing: 8) {
                                GridRow { Text(copy.wouldSend).foregroundStyle(.secondary); Text(copy.cloudPayloadSummary(bytes: proposal.payloadSizeBytes, model: proposal.modelID)) }
                                GridRow { Text(copy.dataLabel).foregroundStyle(.secondary); Text(proposal.dataClasses.joined(separator: ", ")) }
                                GridRow { Text(copy.locationLabel).foregroundStyle(.secondary); Text(proposal.processingLocation) }
                                GridRow { Text(copy.maxCostLabel).foregroundStyle(.secondary); Text(String(format: "$%.6f", proposal.estimatedCost.maximum)) }
                            }
                            Text(copy.taskCloudCredentialHint)
                                .font(.callout).foregroundStyle(.secondary)
                            HStack {
                                Button(copy.approveAndRun) { Task { await approveAndExecute(proposal) } }
                                    .buttonStyle(.borderedProminent)
                                Button(copy.dontSend, role: .cancel) { Task { await rejectProposal(proposal) } }
                            }
                            metadata(copy.proposalOnly, correlation: proposal.correlationID, copy: copy)
                        }
                    case .cloudExecuting:
                        taskBubble(currentTaskPrompt)
                        resultCard(title: copy.taskCloudExecuting, icon: "arrow.up.forward.circle.fill", color: .blue) {
                            ProgressView(copy.cloudExecutingDetail)
                        }
                    case .cloudResult(let text, let model, let cost, let correlation):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: copy.taskCloudCompleted, icon: "checkmark.shield.fill", color: .green) {
                            Text(text).textSelection(.enabled)
                            Text(copy.actualCost(cost))
                                .font(.caption).foregroundStyle(.secondary)
                            metadata(copy.approvedCloudRoute(model), correlation: correlation, copy: copy)
                        }
                    case .denied:
                        taskBubble(currentTaskPrompt)
                        resultCard(title: copy.taskDeniedTitle, icon: "hand.raised.fill", color: .secondary) {
                            Text(copy.taskDeniedBody)
                        }
                    case .unavailable(let message):
                        taskBubble(currentTaskPrompt)
                        resultCard(title: copy.taskUnavailableTitle, icon: "exclamationmark.triangle.fill", color: .orange) {
                            Text(message)
                            Button(copy.openRecoverySettings) { destination = .settings }
                        }
                    case .failed(let message):
                        if !currentTaskPrompt.isEmpty { taskBubble(currentTaskPrompt) }
                        resultCard(title: copy.taskFailedTitle, icon: "xmark.octagon.fill", color: .red) {
                            Text(message).textSelection(.enabled)
                        }
                    }
                }
                .padding(28)
            }
        }
        .background(Color(nsColor: .windowBackgroundColor))
    }

    @MainActor
    private func resetWorkbenchTask() {
        prompt = ""
        currentTaskPrompt = ""
        taskState = .idle
    }

    private func productionAgentActivity(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Label(copy.parallelAgents, systemImage: "rectangle.3.group")
                    .font(.headline)
                Spacer()
                Text(productionAgentActivityStatusLabel(copy))
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            switch agentActivityState {
            case .loading:
                ProgressView().controlSize(.small)
            case .ready(let state) where state.agents.isEmpty:
                Text(productionAgentActivityEmptyMessage(state, copy: copy))
                    .font(.callout)
                    .foregroundStyle(.secondary)
            case .ready(let state):
                ForEach(state.agents, id: \.paneID) { agent in
                    HStack(alignment: .top, spacing: 12) {
                        Image(systemName: agentStatusSymbol(agent.state))
                            .foregroundStyle(agentStatusColor(agent.state))
                            .frame(width: 18)
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text(copy.paneLabel(agent.paneID)).font(.subheadline.weight(.semibold))
                                Spacer()
                                Text(copy.agentStatusLabel(agent.state))
                                    .font(.caption.weight(.medium))
                                    .foregroundStyle(agentStatusColor(agent.state))
                            }
                            Text(copy.workspaceLine(workspace: agent.workspaceID, tab: agent.tabID, terminal: agent.terminalID))
                                .font(.caption2.monospaced())
                                .foregroundStyle(.tertiary)
                                .textSelection(.enabled)
                        }
                    }
                    .padding(12)
                    .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 12))
                }
            }
        }
        .padding(16)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))
    }

    private func productionAgentActivityStatusLabel(_ copy: ProductCopy) -> String {
        switch agentActivityState {
        case .loading: return copy.agentActivityChecking
        case .ready(let state):
            if state.freshness == "fresh" { return copy.agentActivityLive }
            if state.reason == "HERDR_NOT_RUNNING" { return copy.agentActivityHerdrStopped }
            if let reason = state.reason { return copy.agentActivityDisconnected(reason) }
            return copy.agentActivityDisconnectedGeneric
        }
    }

    private func productionAgentActivityEmptyMessage(_ state: RuntimePresentationState, copy: ProductCopy) -> String {
        if state.reason == "HERDR_NOT_RUNNING" { return copy.agentActivityStartRuntime }
        if state.freshness == "fresh" { return copy.agentActivityNone }
        return copy.agentActivityUnavailable
    }

    private func agentStatusSymbol(_ status: String) -> String {
        switch status {
        case "working": "bolt.horizontal.circle.fill"
        case "blocked": "exclamationmark.circle.fill"
        case "idle": "moon.circle.fill"
        case "done": "checkmark.circle.fill"
        default: "questionmark.circle.fill"
        }
    }

    private func agentStatusColor(_ status: String) -> Color {
        switch status {
        case "working": .blue
        case "blocked": .orange
        case "idle": .secondary
        case "done": .green
        default: .secondary
        }
    }

    private func cloudSettingsSection(_ copy: ProductCopy) -> some View {
        GroupBox(copy.optionalCloudAI) {
            VStack(alignment: .leading, spacing: 10) {
                switch cloudSetupState {
                case .loading:
                    ProgressView(copy.checkingCloud)
                case .disabled:
                    Label(copy.cloudOffTitle, systemImage: "cloud.slash")
                    Text(copy.cloudOffDetail)
                        .font(.callout).foregroundStyle(.secondary)
                    SecureField(copy.deepSeekKey, text: $deepSeekAPIKey)
                        .textFieldStyle(.roundedBorder)
                        .accessibilityLabel("DeepSeek API key")
                    Button(copy.saveEnableCloud) { Task { await saveAndEnableCloud() } }
                        .buttonStyle(.borderedProminent)
                        .disabled(deepSeekAPIKey.isEmpty)
                case .enabled(let model):
                    Label(copy.cloudAvailable, systemImage: "checkmark.shield.fill")
                        .foregroundStyle(.green)
                    Text(copy.cloudStored)
                        .font(.callout).foregroundStyle(.secondary)
                    Text(copy.cloudModelApprovalNote(model))
                        .font(.callout).foregroundStyle(.secondary)
                    SecureField(copy.replaceCloudKey, text: $deepSeekAPIKey)
                        .textFieldStyle(.roundedBorder)
                        .accessibilityLabel("Replacement DeepSeek API key")
                    Button(copy.replaceCredential) { Task { await saveAndEnableCloud() } }
                        .disabled(deepSeekAPIKey.isEmpty)
                    Button(copy.disableCloud, role: .destructive) {
                        Task { await disableCloud() }
                    }
                case .saving:
                    ProgressView(copy.updatingCloud)
                case .failed(let message):
                    Label(copy.cloudNeedsAttention, systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                    Button(copy.checkAgain) { Task { await loadCloudSettings() } }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private func routeBadge(_ copy: ProductCopy) -> some View {
        Label(runtimeIndicatorTitle(copy), systemImage: runtimeIndicatorIcon)
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

    private func metadata(_ route: String, correlation: String, copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(route)
            Text(copy.auditCorrelation(correlation)).textSelection(.enabled)
        }
        .font(.caption).foregroundStyle(.secondary)
    }

    private func runtimeIndicatorTitle(_ copy: ProductCopy) -> String {
        switch runtimeState {
        case .running, .sampling, .sample: copy.runtimeReady
        case .starting, .loading: copy.runtimeChecking
        case .stopped: copy.runtimeStopped
        case .degraded: copy.runtimeRecovery
        case .failed: copy.runtimeUnavailable
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
                    if result.finishReason == "accepted" {
                        return .accepted(result.model, result.correlationID)
                    }
                    guard let output = result.output else {
                        return .failed("Local response contained neither acceptance nor output.")
                    }
                    return .localResult(output, result.model, result.correlationID)
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
    private func loadAgentActivity() async {
        guard let context = installationContext() else {
            var provider = RuntimePresentationProvider()
            provider.markDisconnected(reason: "not_connected")
            agentActivityState = .ready(provider.state)
            return
        }
        agentActivityState = await Task.detached { () -> AgentActivityViewState in
            do {
                let snapshot = try SupervisorClient(executableURL: context.supervisor)
                    .herdrSnapshot(rootURL: context.root)
                var provider = RuntimePresentationProvider()
                if snapshot.freshness == "fresh" {
                    try provider.apply(snapshot: snapshot)
                } else {
                    provider.markDisconnected(reason: snapshot.reason ?? "stale")
                }
                return .ready(provider.state)
            } catch {
                var provider = RuntimePresentationProvider()
                provider.markDisconnected(reason: String(describing: error))
                return .ready(provider.state)
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
                    osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
                    architecture: Self.hostArchitecture,
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

    nonisolated private static let hostArchitecture: String = {
        #if arch(arm64)
        return "aarch64"
        #elseif arch(x86_64)
        return "x86_64"
        #else
        return "unknown"
        #endif
    }()

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

enum DailyWorkbenchDestination: Hashable {
    case newTask
    case history
    case settings
}

enum DailyWorkbenchSettingsSection: Hashable {
    case memory
    case agentsTools
    case permissions
    case modelsProviders
    case localRuntime
    case dataPrivacy
    case diagnostics
}
