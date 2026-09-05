import SwiftUI
import LifecycleContract
import SupervisorProtocol
import RuntimeSecurity

enum HistoryRecoveryViewState: Sendable {
    case loading
    case unavailable(String)
    case ready(TaskHistoryReconcilePayload)
    case acting
    case failed(String)
}

struct HistoryRecoveryPanel: View {
    let language: ProductLanguage
    let supervisorURL: URL
    let rootURL: URL

    @State private var state: HistoryRecoveryViewState = .loading
    @State private var selectedTaskID: String?
    @State private var pendingFreshTaskID: String?
    @State private var confirmFreshRun = false

    private let binding = HistoryRecoveryServiceBinding.productDefault

    var body: some View {
        let copy = ProductCopy(language: language)
        VStack(alignment: .leading, spacing: 12) {
            switch state {
            case .loading:
                ProgressView(copy.historyLoading)
            case .unavailable(let message):
                Label(copy.historyUnavailable, systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                Text(message).font(.callout).foregroundStyle(.secondary)
                Text(copy.historyStartRuntimeHint)
                    .font(.caption).foregroundStyle(.secondary)
                Button(copy.tryAgain) { Task { await refresh() } }
            case .ready(let snapshot):
                authorityBanner(snapshot, copy: copy)
                HStack(alignment: .top, spacing: 0) {
                    taskList(snapshot, copy: copy)
                    Divider()
                    taskDetail(snapshot, copy: copy)
                }
                .frame(minHeight: 320)
                HStack {
                    Button(copy.refreshReconcile) { Task { await refresh() } }
                    Spacer()
                    Text(copy.auditPath(binding.auditPath))
                        .font(.caption2.monospaced()).foregroundStyle(.secondary)
                }
            case .acting:
                ProgressView(copy.historyActing)
            case .failed(let message):
                Label(copy.historyFailedSafely, systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
                Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                Button(copy.tryAgain) { Task { await refresh() } }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .task { await refresh() }
        .confirmationDialog(
            copy.freshRunConfirmation,
            isPresented: $confirmFreshRun, titleVisibility: .visible
        ) {
            Button(copy.startFreshRun) {
                if let taskID = pendingFreshTaskID { Task { await freshRun(taskID: taskID) } }
            }
        }
    }

    @ViewBuilder
    private func authorityBanner(_ snapshot: TaskHistoryReconcilePayload, copy: ProductCopy) -> some View {
        HStack(spacing: 8) {
            Label(copy.runtimeAuthority(snapshot.runtimeAuthority), systemImage: "checkmark.shield.fill")
                .foregroundStyle(.green)
            Spacer()
            Text(copy.freshness(snapshot.freshness))
                .font(.caption.monospaced()).foregroundStyle(.secondary)
        }
    }

    @ViewBuilder
    private func taskList(_ snapshot: TaskHistoryReconcilePayload, copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(copy.persistedTasks).font(.headline)
            if snapshot.tasks.isEmpty {
                Text(copy.noPersistedTasks)
                    .font(.callout).foregroundStyle(.secondary)
            } else {
                List(selection: $selectedTaskID) {
                    ForEach(snapshot.tasks, id: \.taskID) { task in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(task.intentLabel).font(.callout.weight(.semibold))
                            Text(task.displayOutcome).font(.caption).foregroundStyle(.secondary)
                        }
                        .tag(task.taskID as String?)
                    }
                }
                .frame(minWidth: 220)
            }
        }
        .padding(12)
        .onAppear {
            if selectedTaskID == nil {
                selectedTaskID = snapshot.tasks.first?.taskID
            }
        }
    }

    @ViewBuilder
    private func taskDetail(_ snapshot: TaskHistoryReconcilePayload, copy: ProductCopy) -> some View {
        if let task = snapshot.tasks.first(where: { $0.taskID == selectedTaskID }) {
            VStack(alignment: .leading, spacing: 14) {
                Text(task.intentLabel).font(.title3.weight(.semibold))
                detailRow(copy.detailLabel(.outcome), task.displayOutcome, copy: copy)
                detailRow(copy.detailLabel(.runtimeState), task.runtimeState, copy: copy)
                detailRow(copy.detailLabel(.revision), String(task.lastAcceptedRevision ?? 0), copy: copy)
                detailRow(copy.detailLabel(.pane), task.herdrPaneID ?? "—", copy: copy)
                if task.reconciliationRequired {
                    Label(copy.reconciliationRequired, systemImage: "exclamationmark.triangle.fill")
                        .font(.callout).foregroundStyle(.orange)
                }
                recoveryActions(for: task, snapshot: snapshot, copy: copy)
            }
            .padding(16)
        } else {
            Text(copy.selectTaskHint)
                .font(.callout).foregroundStyle(.secondary)
                .padding(16)
        }
    }

    @ViewBuilder
    private func recoveryActions(for task: TaskHistoryTaskPayload, snapshot: TaskHistoryReconcilePayload, copy: ProductCopy) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(copy.recoveryHerdrAuthority).font(.headline)
            HStack(spacing: 10) {
                Button(copy.reclaimSession) {
                    Task { await reclaim(taskID: task.taskID) }
                }
                .disabled(!task.mayResume || task.reconciliationRequired || snapshot.freshness != "fresh")
                Button(copy.cancelGracefully) {
                    Task { await cancel(task: task) }
                }
                .disabled(task.reconciliationRequired || snapshot.freshness != "fresh" || !isCancellable(task))
            }
            HStack(spacing: 8) {
                Button(copy.startFreshRun) {
                    pendingFreshTaskID = task.taskID
                    confirmFreshRun = true
                }
                .disabled(
                    !["succeeded", "failed", "cancelled", "blocked", "unknown"].contains(task.runtimeState)
                )
            }
            Text(copy.recoveryRevisionHint)
                .font(.caption).foregroundStyle(.secondary)
        }
    }

    private func detailRow(_ title: String, _ value: String, copy: ProductCopy) -> some View {
        HStack(alignment: .top) {
            Text(title).font(.caption.weight(.semibold)).foregroundStyle(.secondary).frame(width: 110, alignment: .leading)
            Text(value).font(.callout)
        }
    }

    private func isCancellable(_ task: TaskHistoryTaskPayload) -> Bool {
        ["running", "starting", "blocked", "queued"].contains(task.runtimeState)
    }

    @MainActor
    private func refresh() async {
        state = .loading
        do {
            let supervisor = supervisorURL
            let root = rootURL
            let snapshot = try await Task.detached {
                try SupervisorClient(executableURL: supervisor).taskMetadataReconcile(rootURL: root)
            }.value
            state = .ready(snapshot)
        } catch {
            state = .unavailable(String(describing: error))
        }
    }

    @MainActor
    private func reclaim(taskID: String) async {
        state = .acting
        do {
            let supervisor = supervisorURL
            let root = rootURL
            _ = try await Task.detached {
                try SupervisorClient(executableURL: supervisor).taskHistoryReclaim(rootURL: root, taskID: taskID)
            }.value
            await refresh()
        } catch {
            state = .failed(String(describing: error))
        }
    }

    @MainActor
    private func cancel(task: TaskHistoryTaskPayload) async {
        guard let revision = task.lastAcceptedRevision else {
            state = .failed("Missing accepted revision for cancellation.")
            return
        }
        state = .acting
        do {
            let supervisor = supervisorURL
            let root = rootURL
            _ = try await Task.detached {
                try SupervisorClient(executableURL: supervisor)
                    .taskHistoryCancel(rootURL: root, taskID: task.taskID, expectedRevision: revision)
            }.value
            await refresh()
        } catch {
            state = .failed(String(describing: error))
        }
    }

    @MainActor
    private func freshRun(taskID: String) async {
        state = .acting
        do {
            let supervisor = supervisorURL
            let root = rootURL
            _ = try await Task.detached {
                let secrets = try RuntimeSecretCoordinator().ensure()
                return try SupervisorClient(executableURL: supervisor)
                    .taskHistoryFreshRun(rootURL: root, taskID: taskID,
                        omlxAPIKey: secrets.omlxAPIKey, brokerToken: secrets.brokerToken,
                        memoryToken: secrets.memoryToken)
            }.value
            await refresh()
        } catch {
            state = .failed(String(describing: error))
        }
    }
}
