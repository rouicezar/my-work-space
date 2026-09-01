import SwiftUI
import LifecycleContract

struct HistoryRecoveryPreview: View {
    let language: ProductLanguage
    @Binding var selection: HistoryPreviewTaskState
    @State private var decisionPreviewShown = false

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        HStack(spacing: 0) {
            taskList
            Divider()
            taskDetail
        }
        .onChange(of: selection) { _, _ in decisionPreviewShown = false }
    }

    private var taskList: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 5) {
                Text(copy[.historyTitle]).font(.title2.weight(.semibold))
                Text(copy[.historySyntheticOnly]).font(.caption).foregroundStyle(.secondary)
            }
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(HistoryRecoveryPreviewContract.productDefault.states) { state in
                        Button {
                            selection = state
                        } label: {
                            HStack(alignment: .top, spacing: 10) {
                                Image(systemName: symbol(for: state))
                                    .foregroundStyle(tint(for: state)).frame(width: 18)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(copy.taskTitle(state)).font(.callout.weight(.semibold))
                                    Text(copy.stateTitle(state)).font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer(minLength: 0)
                            }
                            .padding(11).contentShape(Rectangle())
                            .background(selection == state ? Color.accentColor.opacity(0.14) : Color.secondary.opacity(0.055), in: RoundedRectangle(cornerRadius: 11))
                            .overlay(RoundedRectangle(cornerRadius: 11).stroke(selection == state ? Color.accentColor.opacity(0.55) : Color.clear))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .padding(20).frame(width: 240).background(.thinMaterial)
    }

    private var taskDetail: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top, spacing: 14) {
                    Image(systemName: symbol(for: selection))
                        .font(.title2).foregroundStyle(tint(for: selection))
                        .frame(width: 42, height: 42).background(tint(for: selection).opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                    VStack(alignment: .leading, spacing: 5) {
                        Text(copy.taskTitle(selection)).font(.title2.weight(.semibold))
                        Text(copy.stateTitle(selection)).font(.callout.weight(.semibold)).foregroundStyle(tint(for: selection))
                    }
                    Spacer()
                    Text(copy[.previewBadge]).font(.caption2.monospaced().weight(.bold))
                        .padding(.horizontal, 8).padding(.vertical, 5)
                        .background(Color.blue.opacity(0.12), in: Capsule()).foregroundStyle(.blue)
                }

                detailCard(copy[.whyThisState], copy.stateReason(selection), "info.circle")

                HStack(alignment: .top, spacing: 12) {
                    metric(copy[.lastVerified], copy.lastVerified(selection), "checkmark.seal")
                    metric(copy[.agentsAndArtifacts], copy.agentSummary(selection), "person.2")
                }

                VStack(alignment: .leading, spacing: 12) {
                    Label(copy[.executionSummary], systemImage: "list.bullet.rectangle").font(.headline)
                    timeline(copy[.timelineGoal], copy[.timelineGoalValue], complete: true)
                    timeline(copy[.timelineWork], copy.timelineWork(selection), complete: selection != .unknown)
                    timeline(copy[.timelineStop], copy.timelineStop(selection), complete: selection == .completed)
                }
                .cardStyle()

                recoveryCard
                detailCard(copy[.truthBoundary], copy[.truthBoundaryBody], "lock.shield")
            }
            .padding(28).frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var recoveryCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label(copy[.recoveryDecision], systemImage: "arrow.counterclockwise.circle").font(.headline)
            Text(copy.recoveryExplanation(selection)).font(.callout).foregroundStyle(.secondary)
            HStack(spacing: 10) {
                if copy.canPreviewRecovery(selection) {
                    Button(copy.recoveryAction(selection)) { decisionPreviewShown.toggle() }
                        .buttonStyle(.borderedProminent)
                }
                Text(copy.recoveryEligibility(selection)).font(.caption.weight(.semibold))
                    .foregroundStyle(copy.canPreviewRecovery(selection) ? Color.orange : Color.secondary)
            }
            if decisionPreviewShown {
                HStack(alignment: .top, spacing: 9) {
                    Image(systemName: "eye.fill").foregroundStyle(.blue)
                    Text(copy[.recoveryPreviewResult]).font(.caption).foregroundStyle(.secondary)
                }
                .padding(11).background(Color.blue.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
            }
        }
        .cardStyle()
    }

    private func detailCard(_ title: String, _ body: String, _ symbol: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: symbol).font(.headline)
            Text(body).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
        }
        .cardStyle()
    }

    private func metric(_ title: String, _ value: String, _ symbol: String) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            Label(title, systemImage: symbol).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
            Text(value).font(.callout.weight(.medium)).fixedSize(horizontal: false, vertical: true)
        }
        .padding(13).frame(maxWidth: .infinity, minHeight: 76, alignment: .topLeading)
        .background(Color.secondary.opacity(0.06), in: RoundedRectangle(cornerRadius: 12))
    }

    private func timeline(_ title: String, _ value: String, complete: Bool) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: complete ? "checkmark.circle.fill" : "circle.dashed")
                .foregroundStyle(complete ? Color.green : Color.secondary)
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.caption.weight(.semibold))
                Text(value).font(.caption).foregroundStyle(.secondary)
            }
        }
    }

    private func symbol(for state: HistoryPreviewTaskState) -> String {
        switch state {
        case .interrupted: "pause.circle.fill"
        case .blocked: "hand.raised.circle.fill"
        case .failed: "xmark.octagon.fill"
        case .partial: "circle.lefthalf.filled"
        case .cancelled: "slash.circle.fill"
        case .completed: "checkmark.circle.fill"
        case .unknown: "questionmark.diamond.fill"
        }
    }

    private func tint(for state: HistoryPreviewTaskState) -> Color {
        switch state {
        case .interrupted, .partial: .orange
        case .blocked: .purple
        case .failed: .red
        case .cancelled, .unknown: .secondary
        case .completed: .green
        }
    }
}

private extension View {
    func cardStyle() -> some View {
        self.padding(16)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.secondary.opacity(0.16)))
    }
}
