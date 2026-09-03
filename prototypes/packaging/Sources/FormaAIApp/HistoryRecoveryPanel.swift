import SwiftUI
import LifecycleContract
import SupervisorProtocol

enum HistoryRecoveryViewState: Sendable {
    case loading
    case unavailable(String)
    case ready(TaskHistoryReconcilePayload)
    case acting
    case failed(String)
}

struct HistoryRecoveryPanel: View {
    let supervisorURL: URL
    let rootURL: URL

    @State private var state: HistoryRecoveryViewState = .loading
    @State private var selectedTaskID: String?
    @State private var freshPaneID: String = ""

    private let binding = HistoryRecoveryServiceBinding.productDefault

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            switch state {
            case .loading:
                ProgressView("Loading reconciled task history…")
            case .unavailable(let message):
                Label("Task history unavailable", systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                Text(message).font(.callout).foregroundStyle(.secondary)
                Text("Start the local runtime and ensure Herdr is running before recovery actions.")
                    .font(.caption).foregroundStyle(.secondary)
                Button("Try again") { Task { await refresh() } }
            case .ready(let snapshot):
                authorityBanner(snapshot)
                HStack(alignment: .top, spacing: 0) {
                    taskList(snapshot)
                    Divider()
                    taskDetail(snapshot)
                }
                .frame(minHeight: 320)
                HStack {
                    Button("Refresh reconcile") { Task { await refresh() } }
                    Spacer()
                    Text("Audit: \(binding.auditPath)")
                        .font(.caption2.monospaced()).foregroundStyle(.secondary)
                }
            case .acting:
                ProgressView("Applying Herdr recovery action…")
            case .failed(let message):
                Label("Recovery failed safely", systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
                Text(message).font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                Button("Try again") { Task { await refresh() } }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .task { await refresh() }
    }

    @ViewBuilder
    private func authorityBanner(_ snapshot: TaskHistoryReconcilePayload) -> some View {
        HStack(spacing: 8) {
            Label("Runtime authority: \(snapshot.runtimeAuthority)", systemImage: "checkmark.shield.fill")
                .foregroundStyle(.green)
            Spacer()
            Text("Freshness: \(snapshot.freshness)")
                .font(.caption.monospaced()).foregroundStyle(.secondary)
        }
    }

    @ViewBuilder
    private func taskList(_ snapshot: TaskHistoryReconcilePayload) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Persisted tasks").font(.headline)
            if snapshot.tasks.isEmpty {
                Text("No persisted task metadata yet.")
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
    private func taskDetail(_ snapshot: TaskHistoryReconcilePayload) -> some View {
        if let task = snapshot.tasks.first(where: { $0.taskID == selectedTaskID }) {
            VStack(alignment: .leading, spacing: 14) {
                Text(task.intentLabel).font(.title3.weight(.semibold))
                detailRow("Outcome", task.displayOutcome)
                detailRow("Runtime state", task.runtimeState)
                detailRow("Revision", String(task.lastAcceptedRevision ?? 0))
                detailRow("Pane", task.herdrPaneID ?? "—")
                if task.reconciliationRequired {
                    Label("Reconciliation required before recovery", systemImage: "exclamationmark.triangle.fill")
                        .font(.callout).foregroundStyle(.orange)
                }
                recoveryActions(for: task, snapshot: snapshot)
            }
            .padding(16)
        } else {
            Text("Select a task to inspect reconciled runtime truth.")
                .font(.callout).foregroundStyle(.secondary)
                .padding(16)
        }
    }

    @ViewBuilder
    private func recoveryActions(for task: TaskHistoryTaskPayload, snapshot: TaskHistoryReconcilePayload) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Recovery (Herdr authority)").font(.headline)
            HStack(spacing: 10) {
                Button("Reclaim session") {
                    Task { await reclaim(taskID: task.taskID) }
                }
                .disabled(!task.mayResume || task.reconciliationRequired || snapshot.freshness != "fresh")
                Button("Cancel gracefully") {
                    Task { await cancel(task: task) }
                }
                .disabled(task.reconciliationRequired || snapshot.freshness != "fresh" || !isCancellable(task))
            }
            HStack(spacing: 8) {
                TextField("Fresh-run pane id", text: $freshPaneID)
                    .textFieldStyle(.roundedBorder)
                Button("Start fresh run") {
                    Task { await freshRun(taskID: task.taskID) }
                }
                .disabled(
                    freshPaneID.isEmpty
                        || freshPaneID == task.herdrPaneID
                        || task.reconciliationRequired
                        || snapshot.freshness != "fresh"
                )
            }
            Text("Recovery routes require a fresh Herdr snapshot and matching revision. The UI never manufactures completion or resumability.")
                .font(.caption).foregroundStyle(.secondary)
        }
    }

    private func detailRow(_ title: String, _ value: String) -> some View {
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
            let snapshot = try SupervisorClient(executableURL: supervisorURL)
                .taskMetadataReconcile(rootURL: rootURL)
            state = .ready(snapshot)
        } catch {
            state = .unavailable(String(describing: error))
        }
    }

    @MainActor
    private func reclaim(taskID: String) async {
        state = .acting
        do {
            _ = try SupervisorClient(executableURL: supervisorURL)
                .taskHistoryReclaim(rootURL: rootURL, taskID: taskID)
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
            _ = try SupervisorClient(executableURL: supervisorURL)
                .taskHistoryCancel(rootURL: rootURL, taskID: task.taskID, expectedRevision: revision)
            await refresh()
        } catch {
            state = .failed(String(describing: error))
        }
    }

    @MainActor
    private func freshRun(taskID: String) async {
        state = .acting
        do {
            _ = try SupervisorClient(executableURL: supervisorURL)
                .taskHistoryFreshRun(rootURL: rootURL, taskID: taskID, freshPaneID: freshPaneID)
            await refresh()
        } catch {
            state = .failed(String(describing: error))
        }
    }
}
