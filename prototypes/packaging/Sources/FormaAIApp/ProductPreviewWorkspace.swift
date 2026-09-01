import SwiftUI
import LifecycleContract

struct ProductPreviewWorkspace: View {
    private let provider = ProductPreviewProvider()
    @State private var scenarioID = "preview-parallel-blocked"

    private var scenario: ProductPreviewScenario {
        provider.scenario(id: scenarioID) ?? provider.scenarios[0]
    }

    var body: some View {
        VStack(spacing: 0) {
            previewDisclosure
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    workspaceHeader
                    if let task = scenario.task {
                        executionRail(task)
                        parallelAgents(task)
                        HStack(alignment: .top, spacing: 16) {
                            approvals(task)
                            artifacts(task)
                        }
                        resultAndEvidence(task)
                    } else {
                        emptyWorkbench
                    }
                }
                .padding(30)
                .frame(maxWidth: 1180, alignment: .leading)
                .frame(maxWidth: .infinity)
            }
            .background(Color(nsColor: .windowBackgroundColor))
        }
        .frame(minWidth: 900, minHeight: 620)
    }

    private var previewDisclosure: some View {
        HStack(spacing: 9) {
            Image(systemName: "eye.trianglebadge.exclamationmark")
            Text(provider.notice).font(.callout.weight(.semibold))
            Spacer()
            Picker("Preview scenario", selection: $scenarioID) {
                ForEach(provider.scenarios) { item in
                    Text(item.title).tag(item.scenarioID)
                }
            }
            .labelsHidden()
            .frame(width: 230)
        }
        .foregroundStyle(.black.opacity(0.78))
        .padding(.horizontal, 20)
        .padding(.vertical, 10)
        .background(Color(red: 0.96, green: 0.76, blue: 0.22))
        .accessibilityElement(children: .combine)
        .accessibilityLabel(provider.notice)
    }

    private var workspaceHeader: some View {
        HStack(alignment: .top, spacing: 24) {
            VStack(alignment: .leading, spacing: 8) {
                Text("TASK / \(scenario.state.label.uppercased())")
                    .font(.caption.monospaced().weight(.semibold))
                    .foregroundStyle(scenario.state.tint)
                Text(scenario.title)
                    .font(.system(size: 30, weight: .semibold, design: .rounded))
                Text(scenario.summary)
                    .font(.body)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: 680, alignment: .leading)
            }
            Spacer()
            if let task = scenario.task {
                VStack(alignment: .trailing, spacing: 6) {
                    Label(task.route.label, systemImage: task.route.symbol)
                        .font(.callout.weight(.semibold))
                    Text(task.id).font(.caption2.monospaced()).foregroundStyle(.tertiary)
                }
                .padding(12)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
            }
        }
    }

    private func executionRail(_ task: PreviewTaskPresentation) -> some View {
        panel("Execution", "point.3.connected.trianglepath.dotted") {
            VStack(alignment: .leading, spacing: 14) {
                Text(task.goal).font(.headline)
                HStack(spacing: 0) {
                    railStep("Goal", "checkmark", .green)
                    connector
                    railStep("Route", task.route.symbol, .blue)
                    connector
                    railStep("Agents", "rectangle.3.group", task.agents.isEmpty ? .secondary : .indigo)
                    connector
                    railStep("Review", "checkmark.shield", task.approvals.isEmpty ? .secondary : .orange)
                    connector
                    railStep("Result", "doc.text.magnifyingglass", scenario.state.tint)
                }
            }
        }
    }

    private func parallelAgents(_ task: PreviewTaskPresentation) -> some View {
        panel("Parallel agents", "rectangle.3.group") {
            if task.agents.isEmpty {
                honestEmpty("No agents in this preview state.")
            } else {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 230), spacing: 12)], spacing: 12) {
                    ForEach(task.agents) { agent in
                        VStack(alignment: .leading, spacing: 10) {
                            HStack {
                                Image(systemName: agent.state.symbol).foregroundStyle(agent.state.tint)
                                Text(agent.role).font(.headline)
                                Spacer()
                                Text(agent.state.label).font(.caption.weight(.semibold)).foregroundStyle(agent.state.tint)
                            }
                            Text(agent.summary).font(.callout).foregroundStyle(.secondary)
                            Text(agent.id).font(.caption2.monospaced()).foregroundStyle(.tertiary)
                        }
                        .padding(14)
                        .background(.quaternary.opacity(0.45), in: RoundedRectangle(cornerRadius: 12))
                    }
                }
            }
        }
    }

    private func approvals(_ task: PreviewTaskPresentation) -> some View {
        panel("Approval scope", "checkmark.shield") {
            if task.approvals.isEmpty {
                honestEmpty("No approval is required in this state.")
            } else {
                ForEach(task.approvals) { approval in
                    VStack(alignment: .leading, spacing: 7) {
                        Label(approval.title, systemImage: "hand.raised.fill").font(.headline).foregroundStyle(.orange)
                        Text(approval.scope).font(.callout)
                        Text("Preview only · show next state, never execute")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .top)
    }

    private func artifacts(_ task: PreviewTaskPresentation) -> some View {
        panel("Artifacts & validation", "shippingbox") {
            if task.artifacts.isEmpty {
                honestEmpty("No artifact has been produced in this state.")
            } else {
                ForEach(task.artifacts) { artifact in
                    HStack {
                        Image(systemName: "doc.richtext")
                        VStack(alignment: .leading) {
                            Text(artifact.title).font(.headline)
                            Text(artifact.id).font(.caption2.monospaced()).foregroundStyle(.tertiary)
                        }
                        Spacer()
                        Label(artifact.validation, systemImage: "checkmark.seal.fill").foregroundStyle(.green)
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .top)
    }

    private func resultAndEvidence(_ task: PreviewTaskPresentation) -> some View {
        panel("Result & unresolved evidence", "doc.text.magnifyingglass") {
            VStack(alignment: .leading, spacing: 12) {
                if let result = task.result {
                    Label("Validated result", systemImage: "checkmark.circle.fill").font(.headline).foregroundStyle(.green)
                    Text(result).textSelection(.enabled)
                } else {
                    honestEmpty("No final result is claimed in this state.")
                }
                if !task.unresolvedItems.isEmpty {
                    Divider()
                    ForEach(task.unresolvedItems, id: \.self) { item in
                        Label(item, systemImage: "exclamationmark.triangle.fill").foregroundStyle(.orange)
                    }
                }
            }
        }
    }

    private var emptyWorkbench: some View {
        VStack(spacing: 14) {
            Image(systemName: "square.and.pencil").font(.system(size: 38, weight: .light))
            Text("Ready for a new task").font(.title2.weight(.semibold))
            Text("This synthetic state contains no user data and performs no action.").foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 360)
    }

    private func panel<Content: View>(_ title: String, _ symbol: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Label(title, systemImage: symbol).font(.headline)
            content()
        }
        .padding(18)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(.separator.opacity(0.55), lineWidth: 1))
    }

    private func railStep(_ title: String, _ symbol: String, _ color: Color) -> some View {
        VStack(spacing: 7) {
            Image(systemName: symbol).foregroundStyle(color).frame(height: 18)
            Text(title).font(.caption.weight(.medium))
        }
        .frame(minWidth: 78)
    }

    private var connector: some View {
        Rectangle().fill(.separator).frame(maxWidth: .infinity, maxHeight: 1)
    }

    private func honestEmpty(_ text: String) -> some View {
        Text(text).font(.callout).foregroundStyle(.secondary)
    }
}

private extension PreviewTaskState {
    var label: String {
        switch self {
        case .empty: "Ready"
        case .completed: "Completed"
        case .blocked: "Blocked"
        case .partial: "Partial"
        case .approvalRequired: "Approval required"
        case .interrupted: "Interrupted"
        case .memoryReview: "Memory review"
        case .unavailable: "Unavailable"
        }
    }

    var tint: Color {
        switch self {
        case .completed: .green
        case .blocked, .approvalRequired, .partial: .orange
        case .interrupted, .unavailable: .red
        case .empty, .memoryReview: .blue
        }
    }
}

private extension PreviewRoute {
    var label: String {
        switch self {
        case .local: "Local"
        case .localParallel: "Local · parallel"
        case .cloudProposal: "Cloud proposal"
        case .governedMemory: "Governed memory"
        case .unavailable: "Unavailable"
        }
    }

    var symbol: String {
        switch self {
        case .local, .localParallel: "laptopcomputer"
        case .cloudProposal: "cloud"
        case .governedMemory: "memorychip"
        case .unavailable: "exclamationmark.triangle"
        }
    }
}

private extension PreviewAgentState {
    var label: String { rawValue.capitalized }
    var symbol: String {
        switch self {
        case .queued: "clock"
        case .running: "waveform.path.ecg"
        case .blocked: "pause.circle.fill"
        case .completed: "checkmark.circle.fill"
        }
    }
    var tint: Color {
        switch self {
        case .queued: .secondary
        case .running: .blue
        case .blocked: .orange
        case .completed: .green
        }
    }
}

#if DEBUG
struct ProductPreviewWorkspace_Previews: PreviewProvider {
    static var previews: some View { ProductPreviewWorkspace() }
}
#endif
