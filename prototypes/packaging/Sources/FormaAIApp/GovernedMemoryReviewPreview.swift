import SwiftUI
import LifecycleContract

struct GovernedMemoryReviewPreview: View {
    let language: ProductLanguage
    @Binding var selection: GovernedMemoryReviewState
    @State private var reviewDecisionShown = false

    private var copy: ProductCopy { ProductCopy(language: language) }

    var body: some View {
        HStack(spacing: 0) {
            recordList
            Divider()
            recordDetail
        }
        .onChange(of: selection) { _, _ in reviewDecisionShown = false }
    }

    private var recordList: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 5) {
                Text(copy[.memoryTitle]).font(.title2.weight(.semibold))
                Text(copy[.memorySyntheticOnly]).font(.caption).foregroundStyle(.secondary)
            }
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(GovernedMemoryReviewContract.productDefault.states) { state in
                        Button {
                            selection = state
                        } label: {
                            HStack(alignment: .top, spacing: 10) {
                                Image(systemName: symbol(for: state))
                                    .foregroundStyle(tint(for: state)).frame(width: 18)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(copy.memoryRecordTitle(state)).font(.callout.weight(.semibold))
                                    Text(copy.memoryStateTitle(state)).font(.caption).foregroundStyle(.secondary)
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
        .padding(20).frame(width: 260).background(.thinMaterial)
    }

    private var recordDetail: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top, spacing: 14) {
                    Image(systemName: symbol(for: selection))
                        .font(.title2).foregroundStyle(tint(for: selection))
                        .frame(width: 42, height: 42).background(tint(for: selection).opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                    VStack(alignment: .leading, spacing: 5) {
                        Text(copy.memoryRecordTitle(selection)).font(.title2.weight(.semibold))
                        Text(copy.memoryStateTitle(selection)).font(.callout.weight(.semibold)).foregroundStyle(tint(for: selection))
                    }
                    Spacer()
                    Text(copy[.memoryPreviewBadge]).font(.caption2.monospaced().weight(.bold))
                        .padding(.horizontal, 8).padding(.vertical, 5)
                        .background(Color.blue.opacity(0.12), in: Capsule()).foregroundStyle(.blue)
                }

                detailCard(copy.memoryRecordTitle(selection), copy.memoryReason(selection), "info.circle")

                provenanceCard

                VStack(alignment: .leading, spacing: 12) {
                    Label(copy[.authorityBoundary], systemImage: "lock.shield").font(.headline)
                    Text(copy[.authorityBoundaryBody]).font(.callout).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .memoryCardStyle()

                HStack(alignment: .top, spacing: 9) {
                    Image(systemName: "eye.fill").foregroundStyle(.blue)
                    Text(copy[.reviewAction]).font(.caption).foregroundStyle(.secondary)
                }
                .padding(11).background(Color.blue.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
            }
            .padding(28).frame(maxWidth: 780, alignment: .leading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var provenanceCard: some View {
        VStack(alignment: .leading, spacing: 13) {
            Label(copy[.provenance], systemImage: "doc.text.magnifyingglass").font(.headline)
            Text(copy.memoryProvenance(selection)).font(.callout.weight(.medium)).foregroundStyle(tint(for: selection))
            VStack(alignment: .leading, spacing: 8) {
                provenanceRow(copy[.claimKey], claimValue(for: selection))
                provenanceRow(copy[.version], versionValue(for: selection))
                provenanceRow(copy[.previousRecord], previousValue(for: selection))
                provenanceRow(copy[.correlation], correlationValue(for: selection))
                provenanceRow(copy[.sources], sourcesValue(for: selection))
            }
        }
        .memoryCardStyle()
    }

    private func provenanceRow(_ title: String, _ value: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Text(title).font(.caption.weight(.semibold)).foregroundStyle(.secondary).frame(width: 120, alignment: .leading)
            Text(value).font(.caption.monospaced()).textSelection(.enabled).fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
    }

    private func detailCard(_ title: String, _ body: String, _ symbol: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: symbol).font(.headline)
            Text(body).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
        }
        .memoryCardStyle()
    }

    private func claimValue(for state: GovernedMemoryReviewState) -> String {
        switch state {
        case .candidate, .confirmed: "sample-product-principle"
        case .conflict: "sample-product-principle (conflict)"
        case .correction: "sample-product-principle (v2)"
        case .deleted: "sample-product-principle (void)"
        }
    }

    private func versionValue(for state: GovernedMemoryReviewState) -> String {
        switch state {
        case .candidate: "not yet stored"
        case .confirmed, .conflict: "1"
        case .correction: "2 (from 1)"
        case .deleted: "n/a"
        }
    }

    private func previousValue(for state: GovernedMemoryReviewState) -> String {
        switch state {
        case .confirmed: "none (first version)"
        case .correction, .deleted: "record-<prior-uuid>"
        case .candidate, .conflict: "none"
        }
    }

    private func correlationValue(for state: GovernedMemoryReviewState) -> String {
        "corr-\(state.rawValue)"
    }

    private func sourcesValue(for state: GovernedMemoryReviewState) -> String {
        switch state {
        case .deleted: "removed · audit trail retained"
        case .candidate, .confirmed, .conflict, .correction: "uri: notes://source-1"
        }
    }

    private func symbol(for state: GovernedMemoryReviewState) -> String {
        switch state {
        case .candidate: "tray.and.arrow.down"
        case .confirmed: "checkmark.seal.fill"
        case .conflict: "exclamationmark.triangle.fill"
        case .correction: "arrow.uturn.backward.circle.fill"
        case .deleted: "trash.fill"
        }
    }

    private func tint(for state: GovernedMemoryReviewState) -> Color {
        switch state {
        case .candidate: .blue
        case .confirmed: .green
        case .conflict: .orange
        case .correction: .purple
        case .deleted: .secondary
        }
    }
}

private extension View {
    func memoryCardStyle() -> some View {
        self.padding(16)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.secondary.opacity(0.16)))
    }
}
