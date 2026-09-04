import SwiftUI
import LifecycleContract

enum FirstRunAssistantMode {
    case preview
    case production
}

struct FirstRunAssistantView: View {
    let mode: FirstRunAssistantMode
    let language: ProductLanguage
    @ObservedObject var preparation: LocalAIPreparationCoordinator
    let onChangeLanguage: () -> Void
    let onComplete: () -> Void

    private let contract = FirstRunSurfaceContract.productDefault
    @State private var selectedStep: FirstRunStep = .welcome

    var body: some View {
        VStack(spacing: 0) {
            if mode == .preview {
                previewDisclosure
            }
            onboarding
        }
        .frame(minWidth: 980, minHeight: 650)
        .task(id: selectedStep) {
            if mode == .production, selectedStep == .prepareLocalAI {
                await preparation.prepareIfNeeded()
            }
        }
    }

    private var previewDisclosure: some View {
        HStack {
            Label("Product Preview · 产品预览 · synthetic data · no runtime action", systemImage: "eye.trianglebadge.exclamationmark")
                .font(.callout.weight(.semibold))
            Spacer()
        }
        .padding(.horizontal, 20).padding(.vertical, 10)
        .background(Color(red: 0.96, green: 0.76, blue: 0.22))
        .foregroundStyle(.black.opacity(0.78))
    }

    private var onboarding: some View {
        let copy = FirstRunCopy(language: language)
        return ResizableWorkbenchLayout(
            sidebarWidth: .constant(300),
            trailingWidth: .constant(0),
            trailingVisible: false,
            sidebar: {
                VStack(alignment: .leading, spacing: 28) {
                    VStack(alignment: .leading, spacing: 8) {
                        Image(systemName: "sparkles.rectangle.stack.fill")
                            .font(.system(size: 30)).foregroundStyle(.blue)
                        Text("Forma AI").font(.title2.weight(.bold))
                        Text(copy.tagline).font(.callout).foregroundStyle(.secondary)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(Array(contract.steps.enumerated()), id: \.element) { index, step in
                            Button { selectedStep = step } label: {
                                HStack(spacing: 12) {
                                    Text("\(index + 1)").font(.caption.monospaced().weight(.bold))
                                        .frame(width: 24, height: 24)
                                        .background(selectedStep == step ? Color.blue : Color.secondary.opacity(0.13), in: Circle())
                                        .foregroundStyle(selectedStep == step ? .white : .secondary)
                                    Text(copy.title(for: step)).font(.callout.weight(selectedStep == step ? .semibold : .regular))
                                    Spacer()
                                }
                                .padding(.vertical, 8).padding(.horizontal, 10).contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    Spacer()
                    Button(copy.changeLanguage, action: onChangeLanguage)
                        .buttonStyle(.plain).font(.caption).foregroundStyle(.secondary)
                }
                .padding(30).background(.thinMaterial)
            },
            content: {
                VStack(alignment: .leading, spacing: 26) {
                    Spacer()
                    Text(copy.eyebrow(for: selectedStep)).font(.caption.monospaced().weight(.bold)).foregroundStyle(.blue)
                    Text(copy.headline(for: selectedStep))
                        .font(.system(size: 36, weight: .semibold, design: .rounded))
                        .frame(maxWidth: 650, alignment: .leading)
                    Text(copy.explanation(for: selectedStep))
                        .font(.title3).foregroundStyle(.secondary)
                        .frame(maxWidth: 650, alignment: .leading)
                    if mode == .production && (selectedStep == .prepareLocalAI || selectedStep == .recommendedModel) {
                        preparationPanel(copy)
                    }
                    HStack(spacing: 12) {
                        readinessCard(copy.privateByDefault, "lock.shield.fill", .green)
                        readinessCard(copy.localAIManaged, "laptopcomputer.and.arrow.down", .blue)
                        readinessCard(copy.cloudOptional, "cloud", .orange)
                    }
                    .frame(maxWidth: 720)
                    Spacer()
                    HStack {
                        Text(mode == .preview ? copy.previewFootnote : copy.productionFootnote)
                            .font(.caption).foregroundStyle(.secondary)
                        Spacer()
                        Button(copy.primaryButton(for: selectedStep, preparationBusy: preparation.isBusy)) {
                            Task { await advance(copy: copy) }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(!canAdvancePrimary(copy: copy))
                    }
                }
                .padding(44).frame(maxWidth: .infinity, alignment: .leading)
            },
            trailing: { EmptyView() }
        )
    }

    @ViewBuilder
    private func preparationPanel(_ copy: FirstRunCopy) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                if preparation.isBusy { ProgressView().controlSize(.small) }
                Text(copy.preparationStatus(preparation.status)).font(.callout)
            }
            if case .downloadingModel(let transferred, let total) = preparation.status, total > 0 {
                ProgressView(value: Double(transferred), total: Double(total))
            }
            if let model = preparation.recommendedModelLabel {
                Text(model).font(.caption.monospaced()).foregroundStyle(.secondary)
            }
            if case .failed = preparation.status {
                Button(copy.firstRunRetry) {
                    Task { await preparation.retry() }
                }
                .buttonStyle(.bordered)
            }
        }
        .padding(16)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
    }

    private func readinessCard(_ title: String, _ symbol: String, _ color: Color) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Image(systemName: symbol).font(.title2).foregroundStyle(color)
            Text(title).font(.headline)
        }
        .padding(16).frame(maxWidth: .infinity, minHeight: 110, alignment: .topLeading)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 15))
        .overlay(RoundedRectangle(cornerRadius: 15).stroke(.separator.opacity(0.5)))
    }

    private func canAdvancePrimary(copy: FirstRunCopy) -> Bool {
        if preparation.isBusy { return false }
        if mode == .production, selectedStep == .createFirstTask { return preparation.isReady }
        return true
    }

    @MainActor
    private func advance(copy: FirstRunCopy) async {
        if mode == .production, selectedStep == .prepareLocalAI {
            await preparation.prepareIfNeeded()
            guard preparation.isReady else { return }
        }
        if selectedStep == .createFirstTask {
            guard mode != .production || preparation.isReady else { return }
            if mode == .production {
                OnboardingPreferences.markComplete(language: language)
            }
            onComplete()
            return
        }
        guard let index = contract.steps.firstIndex(of: selectedStep), index + 1 < contract.steps.count else { return }
        selectedStep = contract.steps[index + 1]
        if mode == .production, selectedStep == .recommendedModel {
            await preparation.prepareIfNeeded()
        }
    }
}
