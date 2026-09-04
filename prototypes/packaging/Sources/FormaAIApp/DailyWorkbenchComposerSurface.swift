import SwiftUI
import LifecycleContract

enum DailyWorkbenchComposerAction {
    case previewPlan
    case submitTask
}

struct DailyWorkbenchComposerSurface: View {
    let language: ProductLanguage
    @Binding var prompt: String
    let action: DailyWorkbenchComposerAction
    let isActionDisabled: Bool
    let onAction: () -> Void
    var onPreviewContext: (() -> Void)?

    @Binding var previewRoute: PreviewComposerRoute
    var modelChoices: [ModelRouteChoice] = []
    @Binding var selectedModelChoice: ModelRouteChoice

    init(
        language: ProductLanguage,
        prompt: Binding<String>,
        previewRoute: Binding<PreviewComposerRoute>,
        isActionDisabled: Bool,
        onAction: @escaping () -> Void,
        onPreviewContext: @escaping () -> Void
    ) {
        self.language = language
        _prompt = prompt
        self.action = .previewPlan
        self.isActionDisabled = isActionDisabled
        self.onAction = onAction
        self.onPreviewContext = onPreviewContext
        _previewRoute = previewRoute
        _selectedModelChoice = .constant(.automaticLocalFirst)
    }

    init(
        language: ProductLanguage,
        prompt: Binding<String>,
        modelChoices: [ModelRouteChoice],
        selectedModelChoice: Binding<ModelRouteChoice>,
        isActionDisabled: Bool,
        onAction: @escaping () -> Void
    ) {
        self.language = language
        _prompt = prompt
        self.action = .submitTask
        self.isActionDisabled = isActionDisabled
        self.onAction = onAction
        self.onPreviewContext = nil
        _previewRoute = .constant(.localFirst)
        self.modelChoices = modelChoices
        _selectedModelChoice = selectedModelChoice
    }

    var body: some View {
        let copy = ProductCopy(language: language)
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(copy[.newTask].uppercased())
                        .font(.caption.monospaced().weight(.bold))
                        .foregroundStyle(.blue)
                    Text(copy[.greeting])
                        .font(.system(size: 32, weight: .semibold, design: .rounded))
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text(copy[.promptTitle]).font(.headline)
                    ZStack(alignment: .topLeading) {
                        if prompt.isEmpty {
                            Text(copy[.promptPlaceholder])
                                .foregroundStyle(.tertiary)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 8)
                                .allowsHitTesting(false)
                        }
                        TextEditor(text: $prompt)
                            .font(.body)
                            .scrollContentBackground(.hidden)
                            .padding(2)
                            .frame(minHeight: 118)
                    }
                    .padding(10)
                    .background(.background, in: RoundedRectangle(cornerRadius: 15))
                    .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.secondary.opacity(0.22)))
                    Text(copy[.promptHint]).font(.caption).foregroundStyle(.secondary)
                }

                contextCard(copy)
                routeCard(copy)

                HStack(alignment: .center, spacing: 14) {
                    Text(actionExplanation(copy))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                    Spacer()
                    Button(actionTitle(copy)) { onAction() }
                        .buttonStyle(.borderedProminent)
                        .disabled(isActionDisabled || prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }

                VStack(alignment: .leading, spacing: 10) {
                    Text(copy[.starterTitle]).font(.headline)
                    ViewThatFits(in: .horizontal) {
                        HStack(spacing: 10) { starterCards(copy) }
                        VStack(spacing: 10) { starterCards(copy) }
                    }
                }
            }
            .padding(32)
            .frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func actionTitle(_ copy: ProductCopy) -> String {
        switch action {
        case .previewPlan: copy[.previewPlan]
        case .submitTask: copy[.startTask]
        }
    }

    private func actionExplanation(_ copy: ProductCopy) -> String {
        switch action {
        case .previewPlan: copy[.previewPlanExplanation]
        case .submitTask: copy[.startTaskExplanation]
        }
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
            .padding(14)
            .frame(maxWidth: .infinity, minHeight: 88, alignment: .topLeading)
            .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 13))
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func contextCard(_ copy: ProductCopy) -> some View {
        HStack(spacing: 14) {
            Image(systemName: "paperclip.circle.fill").font(.title2).foregroundStyle(.blue)
            VStack(alignment: .leading, spacing: 4) {
                Text(copy[.context]).font(.headline)
                Text(copy[.contextExplanation]).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            if let onPreviewContext {
                Button(copy[.previewContext]) { onPreviewContext() }
                    .buttonStyle(.bordered)
            } else {
                Text(copy[.contextUnavailable])
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(16)
        .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 14))
    }

    @ViewBuilder
    private func routeCard(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Label(copy[.route], systemImage: "arrow.triangle.branch").font(.headline)
                Spacer()
                switch action {
                case .previewPlan:
                    Picker(copy[.route], selection: $previewRoute) {
                        Text(copy[.localRoute]).tag(PreviewComposerRoute.localFirst)
                        Text(copy[.cloudRoute]).tag(PreviewComposerRoute.cloudProposal)
                    }
                    .labelsHidden()
                    .pickerStyle(.segmented)
                    .frame(maxWidth: 330)
                case .submitTask:
                    Picker(copy[.route], selection: $selectedModelChoice) {
                        ForEach(modelChoices) { choice in
                            Text(copy.modelRouteTitle(choice)).tag(choice)
                        }
                    }
                    .labelsHidden()
                    .pickerStyle(.menu)
                    .frame(maxWidth: 330)
                }
            }
            Text(routeDetail(copy))
                .font(.callout)
                .foregroundStyle(.secondary)
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "lock.shield.fill").foregroundStyle(.green)
                VStack(alignment: .leading, spacing: 3) {
                    Text(copy[.privacyTitle]).font(.callout.weight(.semibold))
                    Text(copy[.privacyDetail]).font(.caption).foregroundStyle(.secondary)
                }
            }
            if action == .submitTask {
                Text(copy.composerSafetyDescription(selectedModelChoice))
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(18)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 15))
        .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.secondary.opacity(0.18)))
    }

    private func routeDetail(_ copy: ProductCopy) -> String {
        switch action {
        case .previewPlan:
            previewRoute == .localFirst ? copy[.localRouteDetail] : copy[.cloudRouteDetail]
        case .submitTask:
            selectedModelChoice.composerIsExecutionBound
                ? copy.composerSafetyDescription(selectedModelChoice)
                : copy[.routeBindingRequired]
        }
    }
}

enum PreviewComposerRoute: Hashable {
    case localFirst
    case cloudProposal
}

private extension ModelRouteChoice {
    var composerIsExecutionBound: Bool {
        self == .automaticLocalFirst
    }
}
