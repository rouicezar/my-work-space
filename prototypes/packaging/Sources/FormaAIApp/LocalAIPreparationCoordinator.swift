import Foundation
import SupervisorProtocol
import RuntimeSecurity

struct PreparationFailure: Error, Sendable { let message: String }

enum LocalAIPreparationStatus: Sendable, Equatable {
    case idle
    case planningRuntime
    case installingRuntime
    case planningModel
    case downloadingModel(transferred: Int64, total: Int64)
    case linkingModel
    case startingRuntime
    case ready
    case failed(String)
}

@MainActor
final class LocalAIPreparationCoordinator: ObservableObject {
    @Published private(set) var status: LocalAIPreparationStatus = .idle
    @Published private(set) var recommendedModelLabel: String?

    var isBusy: Bool {
        switch status {
        case .planningRuntime, .installingRuntime, .planningModel, .downloadingModel, .linkingModel, .startingRuntime:
            return true
        default:
            return false
        }
    }

    var isReady: Bool {
        if case .ready = status { return true }
        return false
    }

    func prepareIfNeeded() async {
        switch status {
        case .idle, .failed:
            await runPipeline()
        default:
            break
        }
    }

    func retry() async {
        status = .idle
        await runPipeline()
    }

    private func runPipeline() async {
        guard let installation = ProductPaths.installationContext() else {
            status = .failed("Forma AI could not locate its supervisor or installation manifest.")
            return
        }

        status = .planningRuntime
        let planResult: Result<InstallationPlanPayload, PreparationFailure> = await Task.detached {
            do {
                let client = try SupervisorClient(executableURL: installation.supervisor)
                let plan = try client.installationPlan(
                    rootURL: installation.root,
                    osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
                    upstreamsURL: installation.upstreams
                )
                guard plan.schemaVersion == 1, plan.component == "omlx", plan.approvalRequired,
                      plan.artifactSizeBytes > 0, plan.downloadedBytes >= 0,
                      plan.downloadedBytes <= plan.artifactSizeBytes,
                      plan.artifactSHA256.count == 64 else {
                    return .failure(PreparationFailure(message: "The local runtime plan is invalid."))
                }
                if let blocker = plan.cacheBlocker {
                    return .failure(PreparationFailure(message: "The cached installer needs repair: \(blocker)."))
                }
                return .success(plan)
            } catch {
                return .failure(PreparationFailure(message: String(describing: error)))
            }
        }.value

        guard case .success(let installPlan) = planResult else {
            if case .failure(let message) = planResult { status = .failed(message.message) }
            return
        }

        status = .installingRuntime
        let installResult: Result<Void, PreparationFailure> = await Task.detached {
            do {
                let client = try SupervisorClient(executableURL: installation.supervisor)
                let installed = try client.installOMLX(
                    rootURL: installation.root,
                    osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
                    upstreamsURL: installation.upstreams,
                    approvedArtifactSHA256: installPlan.artifactSHA256
                )
                guard installed.schemaVersion == 1 else {
                    return .failure(PreparationFailure(message: "The local runtime installation result is unsupported."))
                }
                return .success(())
            } catch {
                return .failure(PreparationFailure(message: String(describing: error)))
            }
        }.value

        guard case .success = installResult else {
            if case .failure(let message) = installResult { status = .failed(message.message) }
            return
        }

        guard let modelContext = ProductPaths.modelContext() else {
            status = .failed("Forma AI could not prepare model storage or read the pinned model catalog.")
            return
        }

        status = .planningModel
        let modelPlanResult: Result<ModelPlanPayload, PreparationFailure> = await Task.detached {
            do {
                let client = try SupervisorClient(executableURL: modelContext.supervisor)
                let plan = try client.modelPlan(
                    rootURL: modelContext.root,
                    cacheRootURL: modelContext.cacheRoot,
                    catalogURL: modelContext.catalog
                )
                guard plan.schemaVersion == 1, plan.approvalRequired,
                      plan.revision.count == 40, plan.sizeBytes > 0 else {
                    return .failure(PreparationFailure(message: "The recommended model plan is invalid."))
                }
                return .success(plan)
            } catch {
                return .failure(PreparationFailure(message: String(describing: error)))
            }
        }.value

        guard case .success(var modelPlan) = modelPlanResult else {
            if case .failure(let message) = modelPlanResult { status = .failed(message.message) }
            return
        }

        recommendedModelLabel = modelPlan.modelID

        if !modelPlan.availableVerified {
            status = .downloadingModel(transferred: 0, total: modelPlan.sizeBytes)
            let download = await ModelDownloadCoordinator.downloadChatModel(
                context: modelContext,
                approvedRevision: modelPlan.revision
            ) { progress in
                Task { @MainActor in
                    self.status = .downloadingModel(transferred: progress.transferredBytes, total: progress.totalBytes)
                }
            }
            switch download {
            case .completed:
                break
            case .failed(let message):
                status = .failed(message)
                return
            }

            let replanResult: Result<ModelPlanPayload, PreparationFailure> = await Task.detached {
                do {
                    let client = try SupervisorClient(executableURL: modelContext.supervisor)
                    return .success(try client.modelPlan(
                        rootURL: modelContext.root,
                        cacheRootURL: modelContext.cacheRoot,
                        catalogURL: modelContext.catalog
                    ))
                } catch {
                    return .failure(PreparationFailure(message: String(describing: error)))
                }
            }.value
            guard case .success(let replanned) = replanResult, replanned.availableVerified else {
                if case .failure(let message) = replanResult {
                    status = .failed(message.message)
                } else {
                    status = .failed("The downloaded model could not be verified.")
                }
                return
            }
            modelPlan = replanned
            recommendedModelLabel = replanned.modelID
        }

        status = .linkingModel
        let linkResult: Result<Void, PreparationFailure> = await Task.detached {
            do {
                let client = try SupervisorClient(executableURL: modelContext.supervisor)
                let linked = try client.linkModel(
                    rootURL: modelContext.root,
                    cacheRootURL: modelContext.cacheRoot,
                    catalogURL: modelContext.catalog,
                    approvedRevision: modelPlan.revision
                )
                guard linked.schemaVersion == 1,
                      linked.reference.revision == modelPlan.revision else {
                    return .failure(PreparationFailure(message: "The model reference is invalid."))
                }
                return .success(())
            } catch {
                return .failure(PreparationFailure(message: String(describing: error)))
            }
        }.value

        guard case .success = linkResult else {
            if case .failure(let message) = linkResult { status = .failed(message.message) }
            return
        }

        status = .startingRuntime
        let runtimeResult: Result<Void, PreparationFailure> = await Task.detached {
            do {
                let secrets = try RuntimeSecretCoordinator().ensure()
                let client = try SupervisorClient(executableURL: installation.supervisor)
                let result = try client.startRuntime(
                    rootURL: installation.root,
                    osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
                    architecture: ProductPaths.hostArchitecture,
                    omlxAPIKey: secrets.omlxAPIKey,
                    brokerToken: secrets.brokerToken,
                    memoryToken: secrets.memoryToken
                )
                guard result.schemaVersion == 1 else {
                    return .failure(PreparationFailure(message: "The runtime start result is unsupported."))
                }
                return .success(())
            } catch {
                return .failure(PreparationFailure(message: String(describing: error)))
            }
        }.value

        switch runtimeResult {
        case .success:
            status = .ready
        case .failure(let message):
            status = .failed(message.message)
        }
    }
}
