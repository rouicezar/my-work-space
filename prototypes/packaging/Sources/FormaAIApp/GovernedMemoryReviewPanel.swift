import SwiftUI
import LifecycleContract
import SupervisorProtocol
import RuntimeSecurity

enum MemoryReviewViewState: Sendable {
    case loading
    case unavailable(String)
    case ready(MemoryReviewSnapshotPayload)
    case acting
    case failed(String)
}

struct GovernedMemoryReviewPanel: View {
    let language: ProductLanguage
    let supervisorURL: URL
    let rootURL: URL

    @State private var state: MemoryReviewViewState = .loading
    @State private var selectedCandidateID: String?
    @State private var selectedRecordID: String?

    private let binding = GovernedMemoryReviewContract.realServiceBinding

    var body: some View {
        let copy = ProductCopy(language: language)
        GroupBox(copy.memoryReviewTitle) {
            VStack(alignment: .leading, spacing: 12) {
                switch state {
                case .loading:
                    ProgressView(copy.memoryLoading)
                case .unavailable(let message):
                    Label(copy.memoryUnavailable, systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text(message).font(.callout).foregroundStyle(.secondary)
                    Text(copy.memoryStartRuntimeHint)
                        .font(.caption).foregroundStyle(.secondary)
                    Button(copy.tryAgain) { Task { await refresh() } }
                case .ready(let snapshot):
                    authorityBanner(snapshot, copy: copy)
                    HStack(alignment: .top, spacing: 0) {
                        recordList(snapshot, copy: copy)
                        Divider()
                        recordDetail(snapshot, copy: copy)
                    }
                    .frame(minHeight: 280)
                    HStack {
                        Button(copy.refreshSnapshot) { Task { await refresh() } }
                        Spacer()
                        Text(copy.auditPath(binding.auditPath))
                            .font(.caption2.monospaced()).foregroundStyle(.secondary)
                    }
                case .acting:
                    ProgressView(copy.memoryActing)
                case .failed(let message):
                    Label(copy.memoryFailedSafely, systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.red)
                    Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                    Button(copy.tryAgain) { Task { await refresh() } }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .task { await refresh() }
    }

    @ViewBuilder
    private func authorityBanner(_ snapshot: MemoryReviewSnapshotPayload, copy: ProductCopy) -> some View {
        HStack(spacing: 8) {
            Label(copy.confirmedAuthority(snapshot.confirmedAuthority), systemImage: "checkmark.shield.fill")
                .foregroundStyle(.green)
            Spacer()
            Text(copy.loopbackPort(binding.loopbackPort))
                .font(.caption.monospaced()).foregroundStyle(.secondary)
        }
    }

    @ViewBuilder
    private func recordList(_ snapshot: MemoryReviewSnapshotPayload, copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            if !snapshot.pendingCandidates.isEmpty {
                Text(copy.pendingCandidates).font(.headline)
                ForEach(snapshot.pendingCandidates, id: \.candidateID) { candidate in
                    memoryRow(
                        title: candidate.claimKey,
                        subtitle: candidate.status,
                        symbol: "questionmark.circle",
                        tint: .orange,
                        selected: selectedCandidateID == candidate.candidateID
                    ) {
                        selectedCandidateID = candidate.candidateID
                        selectedRecordID = nil
                    }
                }
            }
            if !snapshot.confirmedRecords.isEmpty {
                Text(copy.confirmedRecords).font(.headline)
                    .padding(.top, snapshot.pendingCandidates.isEmpty ? 0 : 6)
                ForEach(snapshot.confirmedRecords, id: \.recordID) { record in
                    memoryRow(
                        title: record.claimKey,
                        subtitle: "v\(record.version) · semantica",
                        symbol: "checkmark.seal.fill",
                        tint: .green,
                        selected: selectedRecordID == record.recordID
                    ) {
                        selectedRecordID = record.recordID
                        selectedCandidateID = nil
                    }
                }
            }
            if snapshot.pendingCandidates.isEmpty && snapshot.confirmedRecords.isEmpty {
                Text(copy.noMemoryRecords)
                    .font(.callout).foregroundStyle(.secondary)
            }
        }
        .padding(16)
        .frame(width: 260, alignment: .leading)
    }

    @ViewBuilder
    private func recordDetail(_ snapshot: MemoryReviewSnapshotPayload, copy: ProductCopy) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                if let candidate = snapshot.pendingCandidates.first(where: { $0.candidateID == selectedCandidateID }) {
                    detailHeader(title: candidate.claimKey, subtitle: candidate.status, symbol: "questionmark.circle", tint: .orange)
                    provenanceBlock(
                        claimKey: candidate.claimKey,
                        content: candidate.content,
                        correlationID: candidate.correlationID,
                        semanticaID: nil,
                        recordID: candidate.candidateID,
                        version: nil
                    )
                    HStack(spacing: 10) {
                        Button(copy.confirmToSemantica) { Task { await confirm(candidate.candidateID) } }
                            .buttonStyle(.borderedProminent)
                        Button(copy.reject, role: .destructive) { Task { await reject(candidate.candidateID) } }
                    }
                } else if let record = snapshot.confirmedRecords.first(where: { $0.recordID == selectedRecordID }) {
                    detailHeader(title: record.claimKey, subtitle: copy.confirmedVersion(record.version), symbol: "checkmark.seal.fill", tint: .green)
                    provenanceBlock(
                        claimKey: record.claimKey,
                        content: record.content,
                        correlationID: record.correlationID,
                        semanticaID: record.semanticaID,
                        recordID: record.recordID,
                        version: String(record.version)
                    )
                } else {
                    Text(copy.selectMemoryRecord)
                        .font(.callout).foregroundStyle(.secondary)
                }
            }
            .padding(20)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func memoryRow(
        title: String,
        subtitle: String,
        symbol: String,
        tint: Color,
        selected: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: symbol).foregroundStyle(tint).frame(width: 18)
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(.callout.weight(.semibold))
                    Text(subtitle).font(.caption).foregroundStyle(.secondary)
                }
                Spacer(minLength: 0)
            }
            .padding(10)
            .background(selected ? Color.accentColor.opacity(0.14) : Color.secondary.opacity(0.055), in: RoundedRectangle(cornerRadius: 10))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(selected ? Color.accentColor.opacity(0.55) : Color.clear))
        }
        .buttonStyle(.plain)
    }

    private func detailHeader(title: String, subtitle: String, symbol: String, tint: Color) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: symbol).font(.title2).foregroundStyle(tint)
                .frame(width: 40, height: 40)
                .background(tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 10))
            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(.title3.weight(.semibold))
                Text(subtitle).font(.callout.weight(.semibold)).foregroundStyle(tint)
            }
        }
    }

    private func provenanceBlock(
        claimKey: String,
        content: String,
        correlationID: String,
        semanticaID: String?,
        recordID: String,
        version: String?
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(content).font(.callout).foregroundStyle(.secondary)
            provenanceRow("Claim key", claimKey)
            if let version { provenanceRow("Version", version) }
            provenanceRow("Correlation", correlationID)
            provenanceRow("Record id", recordID)
            if let semanticaID { provenanceRow("Semantica id", semanticaID) }
        }
        .padding(12)
        .background(Color.secondary.opacity(0.06), in: RoundedRectangle(cornerRadius: 10))
    }

    private func provenanceRow(_ title: String, _ value: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Text(title).font(.caption.weight(.semibold)).foregroundStyle(.secondary).frame(width: 100, alignment: .leading)
            Text(value).font(.caption.monospaced()).textSelection(.enabled)
            Spacer(minLength: 0)
        }
    }

    @MainActor
    private func refresh() async {
        state = .loading
        state = await Task.detached { () -> MemoryReviewViewState in
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                let snapshot = try SupervisorClient(executableURL: supervisorURL).memoryReviewSnapshot(
                    rootURL: rootURL,
                    memoryPort: binding.loopbackPort,
                    memoryToken: secrets.memoryToken
                )
                guard snapshot.schemaVersion == 1 else {
                    return .failed("Unsupported memory review snapshot.")
                }
                guard snapshot.confirmedAuthority == binding.confirmedAuthority else {
                    return .failed("Unexpected memory authority: \(snapshot.confirmedAuthority)")
                }
                return .ready(snapshot)
            } catch {
                return .unavailable(String(describing: error))
            }
        }.value
        if case .ready(let snapshot) = state {
            if selectedCandidateID == nil && selectedRecordID == nil {
                selectedCandidateID = snapshot.pendingCandidates.first?.candidateID
                selectedRecordID = snapshot.confirmedRecords.first?.recordID
            }
        }
    }

    @MainActor
    private func confirm(_ candidateID: String) async {
        state = .acting
        state = await Task.detached { () -> MemoryReviewViewState in
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                _ = try SupervisorClient(executableURL: supervisorURL).memoryReviewConfirm(
                    rootURL: rootURL,
                    candidateID: candidateID,
                    actor: "workbench-reviewer",
                    memoryPort: binding.loopbackPort,
                    memoryToken: secrets.memoryToken
                )
                let snapshot = try SupervisorClient(executableURL: supervisorURL).memoryReviewSnapshot(
                    rootURL: rootURL,
                    memoryPort: binding.loopbackPort,
                    memoryToken: secrets.memoryToken
                )
                return .ready(snapshot)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
        selectedCandidateID = nil
        selectedRecordID = nil
        if case .ready(let snapshot) = state {
            selectedCandidateID = snapshot.pendingCandidates.first?.candidateID
            selectedRecordID = snapshot.confirmedRecords.first?.recordID
        }
    }

    @MainActor
    private func reject(_ candidateID: String) async {
        state = .acting
        state = await Task.detached { () -> MemoryReviewViewState in
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                _ = try SupervisorClient(executableURL: supervisorURL).memoryReviewReject(
                    rootURL: rootURL,
                    candidateID: candidateID,
                    actor: "workbench-reviewer",
                    memoryPort: binding.loopbackPort,
                    memoryToken: secrets.memoryToken
                )
                let snapshot = try SupervisorClient(executableURL: supervisorURL).memoryReviewSnapshot(
                    rootURL: rootURL,
                    memoryPort: binding.loopbackPort,
                    memoryToken: secrets.memoryToken
                )
                return .ready(snapshot)
            } catch {
                return .failed(String(describing: error))
            }
        }.value
        selectedCandidateID = nil
        if case .ready(let snapshot) = state {
            selectedCandidateID = snapshot.pendingCandidates.first?.candidateID
            selectedRecordID = snapshot.confirmedRecords.first?.recordID
        }
    }
}
