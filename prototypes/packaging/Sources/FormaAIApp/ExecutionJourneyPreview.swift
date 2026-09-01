import SwiftUI
import LifecycleContract

struct ExecutionJourneyPreview: View {
    let language: ProductLanguage
    let stage: PreviewTransitionStage
    let goal: String
    let onAdvance: () -> Void
    let onBackToEdit: () -> Void

    private let contract = ComposeToExecutionPreviewContract.productDefault

    var body: some View {
        let copy = ProductCopy(language: language)

        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HStack {
                    VStack(alignment: .leading, spacing: 5) {
                        Text(copy[.journeyPreview].uppercased())
                            .font(.caption.monospaced().weight(.bold)).foregroundStyle(.blue)
                        Text(copy.stageTitle(stage))
                            .font(.system(size: 30, weight: .semibold, design: .rounded))
                    }
                    Spacer()
                    Button(copy[.backToEdit], action: onBackToEdit).buttonStyle(.bordered)
                }

                stageRail(copy)
                goalCard(copy)
                stageContent(copy)

                HStack(alignment: .center, spacing: 14) {
                    Label(copy[.previewStateNotice], systemImage: "eye.trianglebadge.exclamationmark")
                        .font(.caption).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                    Spacer()
                    if stage != .result {
                        Button(nextActionTitle(copy), action: onAdvance)
                            .buttonStyle(.borderedProminent)
                    }
                }
            }
            .padding(30).frame(maxWidth: 820, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func stageRail(_ copy: ProductCopy) -> some View {
        HStack(spacing: 7) {
            ForEach(Array(contract.stages.enumerated()), id: \.element) { index, item in
                let completed = index < currentIndex
                let current = item == stage
                VStack(spacing: 7) {
                    ZStack {
                        Capsule().fill(current ? Color.blue : completed ? Color.green : Color.secondary.opacity(0.13))
                            .frame(height: 5)
                        if current { Capsule().stroke(Color.blue.opacity(0.25), lineWidth: 5).frame(height: 11) }
                    }
                    Text(copy.stageTitle(item))
                        .font(.caption2.weight(current ? .bold : .regular))
                        .foregroundStyle(current ? Color.primary : Color.secondary)
                        .lineLimit(1).minimumScaleFactor(0.72)
                }
                .frame(maxWidth: .infinity)
            }
        }
        .padding(.vertical, 4)
    }

    private func goalCard(_ copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            Text(copy[.syntheticGoal].uppercased())
                .font(.caption2.monospaced().weight(.bold)).foregroundStyle(.secondary)
            Text(goal).font(.headline).fixedSize(horizontal: false, vertical: true)
        }
        .padding(15).frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.blue.opacity(0.07), in: RoundedRectangle(cornerRadius: 13))
        .overlay(RoundedRectangle(cornerRadius: 13).stroke(Color.blue.opacity(0.16)))
    }

    @ViewBuilder
    private func stageContent(_ copy: ProductCopy) -> some View {
        switch stage {
        case .compose:
            EmptyView()
        case .routeReview:
            headline(copy[.routeHeadline], copy[.routeBody])
            HStack(spacing: 12) {
                evidenceTile(copy[.routeLocalReason], "laptopcomputer", .blue)
                evidenceTile(copy[.routeCloudBoundary], "lock.shield.fill", .green)
            }
        case .plan:
            headline(copy[.planHeadline], copy[.planBody])
            VStack(spacing: 10) {
                numberedStep(1, copy[.planResearch], "books.vertical")
                numberedStep(2, copy[.planAnalyze], "point.3.connected.trianglepath.dotted")
                numberedStep(3, copy[.planDraft], "doc.richtext")
            }
        case .parallelExecution:
            headline(copy[.parallelHeadline], copy[.parallelBody])
            HStack(spacing: 10) {
                agentCard(copy[.agentResearch], copy[.statusComplete], "checkmark.circle.fill", .green)
                agentCard(copy[.agentAnalysis], copy[.statusRunningPreview], "waveform.path.ecg", .blue)
                agentCard(copy[.agentDraft], copy[.statusQueuedPreview], "clock", .orange)
            }
        case .approval:
            headline(copy[.approvalHeadline], copy[.approvalBody])
            VStack(alignment: .leading, spacing: 14) {
                approvalRow(copy[.approvalAction], copy[.approvalScope])
                Divider()
                approvalRow(copy[.approvalDestination], copy[.approvalDestinationValue])
                Divider()
                approvalRow(copy[.approvalEffectLabel], copy[.approvalEffect])
                Label(copy[.approvalPreviewOnly], systemImage: "hand.raised.fill")
                    .font(.caption).foregroundStyle(.orange)
            }
            .padding(18).background(Color.orange.opacity(0.08), in: RoundedRectangle(cornerRadius: 15))
            .overlay(RoundedRectangle(cornerRadius: 15).stroke(Color.orange.opacity(0.22)))
        case .validation:
            headline(copy[.validationHeadline], copy[.validationBody])
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 10) {
                    artifactRow(copy[.artifactNotes], "doc.text")
                    artifactRow(copy[.artifactBrief], "doc.richtext")
                }
                .panelStyle()
                VStack(alignment: .leading, spacing: 10) {
                    validationRow(copy[.checkSources], copy[.valid])
                    validationRow(copy[.checkStructure], copy[.valid])
                    validationRow(copy[.checkPrivacy], copy[.valid])
                }
                .panelStyle()
            }
        case .result:
            headline(copy[.resultHeadline], copy[.resultBody])
            VStack(alignment: .leading, spacing: 16) {
                Label(copy[.resultSummary], systemImage: "checkmark.seal.fill")
                    .font(.title3.weight(.semibold)).foregroundStyle(.primary)
                Divider()
                Label(copy[.resultEvidence], systemImage: "doc.on.doc")
                    .font(.callout).foregroundStyle(.secondary)
                HStack {
                    Text(copy[.resultUnresolved]).font(.callout.weight(.semibold))
                    Spacer()
                    Text(copy[.none]).font(.callout).foregroundStyle(.green)
                }
            }
            .padding(20).background(Color.green.opacity(0.08), in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.green.opacity(0.22)))
        }
    }

    private func headline(_ title: String, _ body: String) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            Text(title).font(.title2.weight(.semibold))
            Text(body).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
        }
    }

    private func evidenceTile(_ text: String, _ symbol: String, _ color: Color) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: symbol).foregroundStyle(color)
            Text(text).font(.callout.weight(.medium)).fixedSize(horizontal: false, vertical: true)
        }
        .padding(16).frame(maxWidth: .infinity, minHeight: 82, alignment: .topLeading)
        .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 13))
    }

    private func numberedStep(_ number: Int, _ text: String, _ symbol: String) -> some View {
        HStack(spacing: 13) {
            Text("\(number)").font(.caption.monospaced().weight(.bold)).foregroundStyle(.white)
                .frame(width: 25, height: 25).background(Color.blue, in: Circle())
            Image(systemName: symbol).foregroundStyle(.secondary).frame(width: 20)
            Text(text).font(.callout.weight(.medium))
            Spacer()
        }
        .padding(13).background(Color.secondary.opacity(0.06), in: RoundedRectangle(cornerRadius: 12))
    }

    private func agentCard(_ role: String, _ status: String, _ symbol: String, _ color: Color) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Image(systemName: symbol).font(.title3).foregroundStyle(color)
            Text(role).font(.headline)
            Text(status).font(.caption).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
        }
        .padding(15).frame(maxWidth: .infinity, minHeight: 115, alignment: .topLeading)
        .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 13))
    }

    private func approvalRow(_ label: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(label).font(.caption.weight(.semibold)).foregroundStyle(.secondary).frame(width: 120, alignment: .leading)
            Text(value).font(.callout.weight(.medium)).fixedSize(horizontal: false, vertical: true)
            Spacer()
        }
    }

    private func artifactRow(_ title: String, _ symbol: String) -> some View {
        Label(title, systemImage: symbol).font(.callout.weight(.medium))
    }

    private func validationRow(_ title: String, _ status: String) -> some View {
        HStack {
            Label(title, systemImage: "checkmark.circle.fill").foregroundStyle(.green)
            Spacer()
            Text(status).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
        }
    }

    private var currentIndex: Int {
        contract.stages.firstIndex(of: stage) ?? 0
    }

    private func nextActionTitle(_ copy: ProductCopy) -> String {
        switch stage {
        case .approval: copy[.showApprovedPreview]
        case .parallelExecution: copy[.nextPreview]
        case .validation: copy[.showResultPreview]
        default: copy[.nextPreview]
        }
    }
}

private extension View {
    func panelStyle() -> some View {
        padding(16)
            .frame(maxWidth: .infinity, alignment: .topLeading)
            .background(Color.secondary.opacity(0.07), in: RoundedRectangle(cornerRadius: 13))
    }
}
