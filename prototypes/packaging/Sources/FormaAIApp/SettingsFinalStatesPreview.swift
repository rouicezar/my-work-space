import SwiftUI
import LifecycleContract

struct ModelsProvidersPreview: View {
    let language: ProductLanguage
    @Binding var selection: ModelRouteState

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        HStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 14) {
                VStack(alignment: .leading, spacing: 5) {
                    Text(copy[.modelsProvidersTitle]).font(.title2.weight(.semibold))
                    Text(copy[.modelsProvidersSyntheticOnly]).font(.caption).foregroundStyle(.secondary)
                }
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(ModelsProvidersContract.productDefault.routeStates) { state in
                            Button {
                                selection = state
                            } label: {
                                HStack(alignment: .top, spacing: 10) {
                                    Image(systemName: symbol(for: state))
                                        .foregroundStyle(tint(for: state)).frame(width: 18)
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(copy.modelRouteTitle(state)).font(.callout.weight(.semibold))
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
            .padding(20).frame(width: 250).background(.thinMaterial)
            Divider()
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    HStack(alignment: .top, spacing: 14) {
                        Image(systemName: symbol(for: selection))
                            .font(.title2).foregroundStyle(tint(for: selection))
                            .frame(width: 42, height: 42).background(tint(for: selection).opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                        VStack(alignment: .leading, spacing: 5) {
                            Text(copy.modelRouteTitle(selection)).font(.title2.weight(.semibold))
                        }
                        Spacer()
                        Text(copy[.modelsProvidersPreviewBadge]).font(.caption2.monospaced().weight(.bold))
                            .padding(.horizontal, 8).padding(.vertical, 5)
                            .background(Color.blue.opacity(0.12), in: Capsule()).foregroundStyle(.blue)
                    }
                    detailCard(copy.modelRouteTitle(selection), copy.modelRouteDetail(selection), "info.circle")
                    boundaryCard(copy[.modelsProvidersBoundary], copy[.modelsProvidersBoundaryBody])
                }
                .padding(28).frame(maxWidth: 760, alignment: .leading)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private func symbol(for state: ModelRouteState) -> String {
        switch state {
        case .automaticLocalFirst: "arrow.triangle.branch"
        case .localOnly: "internaldrive"
        case .cloudWithApproval: "cloud"
        }
    }

    private func tint(for state: ModelRouteState) -> Color {
        switch state {
        case .automaticLocalFirst: .green
        case .localOnly: .blue
        case .cloudWithApproval: .purple
        }
    }
}

struct LocalRuntimePreview: View {
    let language: ProductLanguage
    @Binding var selection: RuntimeFinalState

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        HStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 14) {
                VStack(alignment: .leading, spacing: 5) {
                    Text(copy[.localRuntimeTitle]).font(.title2.weight(.semibold))
                    Text(copy[.localRuntimeSyntheticOnly]).font(.caption).foregroundStyle(.secondary)
                }
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(LocalRuntimeContract.productDefault.states) { state in
                            Button {
                                selection = state
                            } label: {
                                HStack(alignment: .top, spacing: 10) {
                                    Image(systemName: symbol(for: state))
                                        .foregroundStyle(tint(for: state)).frame(width: 18)
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(copy.runtimeStateTitle(state)).font(.callout.weight(.semibold))
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
            .padding(20).frame(width: 250).background(.thinMaterial)
            Divider()
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    HStack(alignment: .top, spacing: 14) {
                        Image(systemName: symbol(for: selection))
                            .font(.title2).foregroundStyle(tint(for: selection))
                            .frame(width: 42, height: 42).background(tint(for: selection).opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                        VStack(alignment: .leading, spacing: 5) {
                            Text(copy.runtimeStateTitle(selection)).font(.title2.weight(.semibold))
                        }
                        Spacer()
                        Text(copy[.localRuntimePreviewBadge]).font(.caption2.monospaced().weight(.bold))
                            .padding(.horizontal, 8).padding(.vertical, 5)
                            .background(Color.blue.opacity(0.12), in: Capsule()).foregroundStyle(.blue)
                    }
                    detailCard(copy.runtimeStateTitle(selection), copy.runtimeStateDetail(selection), "info.circle")
                    boundaryCard(copy[.localRuntimeBoundary], copy[.localRuntimeBoundaryBody])
                }
                .padding(28).frame(maxWidth: 760, alignment: .leading)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private func symbol(for state: RuntimeFinalState) -> String {
        switch state {
        case .stopped: "stop.circle"
        case .starting: "arrow.clockwise.circle"
        case .running: "checkmark.circle.fill"
        case .degraded: "exclamationmark.triangle.fill"
        case .failed: "xmark.octagon.fill"
        }
    }

    private func tint(for state: RuntimeFinalState) -> Color {
        switch state {
        case .stopped: .secondary
        case .starting: .blue
        case .running: .green
        case .degraded: .orange
        case .failed: .red
        }
    }
}

struct DataPrivacyPreview: View {
    let language: ProductLanguage

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        staticSettingsPreview(
            title: copy[.dataPrivacyTitle],
            subtitle: copy[.dataPrivacySyntheticOnly],
            badge: copy[.dataPrivacyPreviewBadge],
            boundaryTitle: copy[.dataPrivacyBoundary],
            boundaryBody: copy[.dataPrivacyBoundaryBody],
            symbol: "lock.shield"
        )
    }
}

struct DiagnosticsRecoveryPreview: View {
    let language: ProductLanguage

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        staticSettingsPreview(
            title: copy[.diagnosticsTitle],
            subtitle: copy[.diagnosticsSyntheticOnly],
            badge: copy[.diagnosticsPreviewBadge],
            boundaryTitle: copy[.diagnosticsBoundary],
            boundaryBody: copy[.diagnosticsBoundaryBody],
            symbol: "wrench.and.screwdriver"
        )
    }
}

@MainActor
private func detailCard(_ title: String, _ body: String, _ symbol: String) -> some View {
    VStack(alignment: .leading, spacing: 8) {
        Label(title, systemImage: symbol).font(.headline)
        Text(body).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
    }
    .cardStyle()
}

@MainActor
private func boundaryCard(_ title: String, _ body: String) -> some View {
    VStack(alignment: .leading, spacing: 12) {
        Label(title, systemImage: "lock.shield").font(.headline)
        Text(body).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
    }
    .cardStyle()
}

@MainActor
private func staticSettingsPreview(
    title: String,
    subtitle: String,
    badge: String,
    boundaryTitle: String,
    boundaryBody: String,
    symbol: String
) -> some View {
    ScrollView {
        VStack(alignment: .leading, spacing: 18) {
            HStack(alignment: .top, spacing: 14) {
                Image(systemName: symbol)
                    .font(.title2).foregroundStyle(.blue)
                    .frame(width: 42, height: 42).background(Color.blue.opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                VStack(alignment: .leading, spacing: 5) {
                    Text(title).font(.title2.weight(.semibold))
                    Text(subtitle).font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Text(badge).font(.caption2.monospaced().weight(.bold))
                    .padding(.horizontal, 8).padding(.vertical, 5)
                    .background(Color.blue.opacity(0.12), in: Capsule()).foregroundStyle(.blue)
            }
            VStack(alignment: .leading, spacing: 12) {
                Label(boundaryTitle, systemImage: "lock.shield").font(.headline)
                Text(boundaryBody).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
            }
            .cardStyle()
        }
        .padding(28).frame(maxWidth: 760, alignment: .leading)
    }
    .frame(maxWidth: .infinity, maxHeight: .infinity)
}

private extension View {
    func cardStyle() -> some View {
        self.padding(16)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.secondary.opacity(0.16)))
    }
}
