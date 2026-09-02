import SwiftUI
import LifecycleContract

struct AgentsToolsPreview: View {
    let language: ProductLanguage
    @Binding var selection: AgentAdapterKind

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        HStack(spacing: 0) {
            agentList
            Divider()
            agentDetail
        }
    }

    private var agentList: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 5) {
                Text(copy[.agentsToolsTitle]).font(.title2.weight(.semibold))
                Text(copy[.agentsToolsSyntheticOnly]).font(.caption).foregroundStyle(.secondary)
            }
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(AgentsToolsContract.productDefault.agentKinds) { kind in
                        Button {
                            selection = kind
                        } label: {
                            HStack(alignment: .top, spacing: 10) {
                                Image(systemName: symbol(for: kind))
                                    .foregroundStyle(tint(for: kind)).frame(width: 18)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(copy.agentKindTitle(kind)).font(.callout.weight(.semibold))
                                    Text(kind == .herdrTerminal ? authorityLabel : adapterLabel)
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer(minLength: 0)
                            }
                            .padding(11).contentShape(Rectangle())
                            .background(selection == kind ? Color.accentColor.opacity(0.14) : Color.secondary.opacity(0.055), in: RoundedRectangle(cornerRadius: 11))
                            .overlay(RoundedRectangle(cornerRadius: 11).stroke(selection == kind ? Color.accentColor.opacity(0.55) : Color.clear))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .padding(20).frame(width: 250).background(.thinMaterial)
    }

    private var agentDetail: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top, spacing: 14) {
                    Image(systemName: symbol(for: selection))
                        .font(.title2).foregroundStyle(tint(for: selection))
                        .frame(width: 42, height: 42).background(tint(for: selection).opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                    VStack(alignment: .leading, spacing: 5) {
                        Text(copy.agentKindTitle(selection)).font(.title2.weight(.semibold))
                        Text(selection == .herdrTerminal ? authorityLabel : adapterLabel)
                            .font(.callout.weight(.semibold)).foregroundStyle(tint(for: selection))
                    }
                    Spacer()
                    Text(copy[.previewBadge]).font(.caption2.monospaced().weight(.bold))
                        .padding(.horizontal, 8).padding(.vertical, 5)
                        .background(Color.blue.opacity(0.12), in: Capsule()).foregroundStyle(.blue)
                }

                detailCard(copy.agentKindTitle(selection), copy.agentKindDetail(selection), "info.circle")

                VStack(alignment: .leading, spacing: 12) {
                    Label(copy[.requiredOperations], systemImage: "list.bullet.rectangle").font(.headline)
                    ForEach(AgentsToolsContract.productDefault.requiredOperations, id: \.self) { operation in
                        HStack(spacing: 10) {
                            Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                            Text(operation).font(.callout.monospaced())
                            Spacer(minLength: 0)
                        }
                    }
                }
                .cardStyle()

                VStack(alignment: .leading, spacing: 12) {
                    Label(copy[.authorityBoundary], systemImage: "lock.shield").font(.headline)
                    Text(copy[.authorityBoundaryBody]).font(.callout).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .cardStyle()
            }
            .padding(28).frame(maxWidth: 760, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func detailCard(_ title: String, _ body: String, _ symbol: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: symbol).font(.headline)
            Text(body).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
        }
        .cardStyle()
    }

    private var authorityLabel: String {
        language == .simplifiedChinese ? "权威执行运行时" : "Authoritative execution runtime"
    }

    private var adapterLabel: String {
        language == .simplifiedChinese ? "适配器" : "Adapter"
    }

    private func symbol(for kind: AgentAdapterKind) -> String {
        switch kind {
        case .herdrTerminal: "terminal.fill"
        case .codexCompatible: "sparkles.rectangle.stack.fill"
        case .claudeCompatible: "star.bubble.fill"
        case .holaOSReference: "square.stack.3d.up.fill"
        }
    }

    private func tint(for kind: AgentAdapterKind) -> Color {
        switch kind {
        case .herdrTerminal: .green
        case .codexCompatible: .blue
        case .claudeCompatible: .purple
        case .holaOSReference: .orange
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
