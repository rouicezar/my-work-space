import SwiftUI
import LifecycleContract

struct DailyWorkbenchPreview: View {
    private let contract = DailyWorkbenchSurfaceContract.productDefault
    @State private var language: ProductLanguage = .simplifiedChinese
    @State private var prompt = ""
    @State private var route: PreviewComposerRoute = .localFirst
    @State private var supervisionExpanded = true
    @State private var contextPreviewPresented = false
    @State private var transitionStage: PreviewTransitionStage = .compose
    @State private var destination: PreviewDestination = .newTask
    @State private var historySelection: HistoryPreviewTaskState = .interrupted
    @State private var memorySelection: GovernedMemoryReviewState = .candidate
    @State private var settingsSection: PreviewSettingsSection = .memory
    @State private var agentSelection: AgentAdapterKind = .herdrTerminal
    @State private var permissionSelection: PermissionScope = .write

    var body: some View {
        let copy = ProductCopy(language: language)

        VStack(spacing: 0) {
            previewDisclosure(copy)
            HStack(spacing: 0) {
                sidebar(copy)
                Divider()
                mainContent(copy)
                if supervisionExpanded {
                    Divider()
                    supervisionRail(copy)
                        .transition(.move(edge: .trailing).combined(with: .opacity))
                }
            }
        }
        .frame(minWidth: 900, minHeight: 620)
        .animation(.easeInOut(duration: 0.18), value: supervisionExpanded)
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
            HistoryRecoveryPreview(language: language, selection: $historySelection)
        } else if transitionStage == .compose {
            composer(copy)
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
                Spacer()
            }
            .padding(16).frame(width: 170).background(.thinMaterial)
            Divider()
            settingsSectionContent
        }
    }

    private func settingsSectionRow(_ section: PreviewSettingsSection, _ title: String, _ symbol: String) -> some View {
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
    private var settingsSectionContent: some View {
        switch settingsSection {
        case .memory:
            GovernedMemoryReviewPreview(language: language, selection: $memorySelection)
        case .agentsTools:
            AgentsToolsPreview(language: language, selection: $agentSelection)
        case .permissions:
            PermissionsPreview(language: language, selection: $permissionSelection)
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
        .padding(22).frame(width: 230).background(.thinMaterial)
    }

    private func navigationRow(_ title: String, _ symbol: String, destination target: PreviewDestination?) -> some View {
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

    private func composer(_ copy: ProductCopy) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(copy[.newTask].uppercased())
                        .font(.caption.monospaced().weight(.bold)).foregroundStyle(.blue)
                    Text(copy[.greeting])
                        .font(.system(size: 32, weight: .semibold, design: .rounded))
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text(copy[.promptTitle]).font(.headline)
                    ZStack(alignment: .topLeading) {
                        if prompt.isEmpty {
                            Text(copy[.promptPlaceholder])
                                .foregroundStyle(.tertiary).padding(.horizontal, 6).padding(.vertical, 8)
                                .allowsHitTesting(false)
                        }
                        TextEditor(text: $prompt)
                            .font(.body).scrollContentBackground(.hidden)
                            .padding(2).frame(minHeight: 118)
                    }
                    .padding(10)
                    .background(.background, in: RoundedRectangle(cornerRadius: 15))
                    .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.secondary.opacity(0.22)))
                    Text(copy[.promptHint]).font(.caption).foregroundStyle(.secondary)
                }

                contextCard(copy)
                routeCard(copy)

                HStack(alignment: .center, spacing: 14) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(copy[.previewPlanExplanation]).font(.caption).foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    Spacer()
                    Button(copy[.previewPlan]) { transitionStage = .routeReview }
                        .buttonStyle(.borderedProminent).disabled(prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }

                VStack(alignment: .leading, spacing: 10) {
                    Text(copy[.starterTitle]).font(.headline)
                    ViewThatFits(in: .horizontal) {
                        HStack(spacing: 10) { starterCards(copy) }
                        VStack(spacing: 10) { starterCards(copy) }
                    }
                }
            }
            .padding(32).frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    @ViewBuilder
    private func starterCards(_ copy: ProductCopy) -> some View {
        starterCard(copy[.starterResearch], "books.vertical") { prompt = copy[.starterResearch] }
        starterCard(copy[.starterWriting], "doc.richtext") { prompt = copy[.starterWriting] }
        starterCard(copy[.starterPlanning], "point.3.connected.trianglepath.dotted") { prompt = copy[.starterPlanning] }
    }

    private func starterCard(_ title: String, _ symbol: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 10) {
                Image(systemName: symbol).foregroundStyle(.blue)
                Text(title).font(.callout.weight(.medium)).fixedSize(horizontal: false, vertical: true)
            }
            .padding(14).frame(maxWidth: .infinity, minHeight: 88, alignment: .topLeading)
            .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 13))
        }
        .buttonStyle(.plain)
    }

    private func contextCard(_ copy: ProductCopy) -> some View {
        HStack(spacing: 14) {
            Image(systemName: "paperclip.circle.fill").font(.title2).foregroundStyle(.blue)
            VStack(alignment: .leading, spacing: 4) {
                Text(copy[.context]).font(.headline)
                Text(copy[.contextExplanation]).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Button(copy[.previewContext]) { contextPreviewPresented = true }
                .buttonStyle(.bordered)
        }
        .padding(16).background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 14))
    }

    private func routeCard(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Label(copy[.route], systemImage: "arrow.triangle.branch").font(.headline)
                Spacer()
                Picker(copy[.route], selection: $route) {
                    Text(copy[.localRoute]).tag(PreviewComposerRoute.localFirst)
                    Text(copy[.cloudRoute]).tag(PreviewComposerRoute.cloudProposal)
                }
                .labelsHidden().pickerStyle(.segmented).frame(maxWidth: 330)
            }
            Text(route == .localFirst ? copy[.localRouteDetail] : copy[.cloudRouteDetail])
                .font(.callout).foregroundStyle(.secondary)
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "lock.shield.fill").foregroundStyle(.green)
                VStack(alignment: .leading, spacing: 3) {
                    Text(copy[.privacyTitle]).font(.callout.weight(.semibold))
                    Text(copy[.privacyDetail]).font(.caption).foregroundStyle(.secondary)
                }
            }
        }
        .padding(18).background(.regularMaterial, in: RoundedRectangle(cornerRadius: 15))
        .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.secondary.opacity(0.18)))
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
            Spacer()
        }
        .padding(20).frame(width: 270).background(.ultraThinMaterial)
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
        }
    }

    private var settingsSectionTitle: String {
        let copy = ProductCopy(language: language)
        switch settingsSection {
        case .memory: return copy.memoryStateTitle(memorySelection)
        case .agentsTools: return copy.agentKindTitle(agentSelection)
        case .permissions: return copy.permissionScopeTitle(permissionSelection)
        }
    }

    private var settingsSectionSummary: String {
        let copy = ProductCopy(language: language)
        switch settingsSection {
        case .memory: return copy[.memorySyntheticOnly]
        case .agentsTools: return copy[.agentsToolsSyntheticOnly]
        case .permissions: return copy[.permissionsSyntheticOnly]
        }
    }

    private var settingsSectionStatus: String {
        let copy = ProductCopy(language: language)
        switch settingsSection {
        case .memory: return copy.memoryProvenance(memorySelection)
        case .agentsTools: return copy.agentKindDetail(agentSelection)
        case .permissions: return copy.permissionScopeDetail(permissionSelection)
        }
    }

    private func advanceTransition() {
        let stages = ComposeToExecutionPreviewContract.productDefault.stages
        guard let index = stages.firstIndex(of: transitionStage), index + 1 < stages.count else { return }
        transitionStage = stages[index + 1]
    }
}

private enum PreviewComposerRoute: Hashable {
    case localFirst
    case cloudProposal
}

private enum PreviewDestination: Hashable {
    case newTask
    case history
    case settings
}

private enum PreviewSettingsSection: Hashable {
    case memory
    case agentsTools
    case permissions
}
