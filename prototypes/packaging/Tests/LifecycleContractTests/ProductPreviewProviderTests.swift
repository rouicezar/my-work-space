import Testing
@testable import LifecycleContract

@Test func productPreviewProviderExposesAllDeterministicReadOnlyScenarios() {
    let provider = ProductPreviewProvider()

    #expect(provider.notice == "Product Preview · synthetic data · no runtime action")
    #expect(provider.scenarios.map(\.scenarioID) == [
        "preview-empty-workbench",
        "preview-local-complete",
        "preview-parallel-blocked",
        "preview-partial-evidence",
        "preview-cloud-proposal",
        "preview-interrupted-recovery",
        "preview-memory-governance",
        "preview-component-unavailable",
    ])
    #expect(provider.scenarios.allSatisfy { $0.schemaVersion == 1 })
    #expect(provider.scenarios.allSatisfy { $0.scenarioID.hasPrefix("preview-") })
    #expect(provider.scenarios.allSatisfy { $0.notice == provider.notice })
    #expect(Set(provider.scenarios.map(\.state)) == Set(PreviewTaskState.allCases))
}

@Test func productPreviewProviderContainsNoProductionCommandsOrExternalDependencies() {
    let provider = ProductPreviewProvider()
    let parallel = provider.scenario(id: "preview-parallel-blocked")
    let cloud = provider.scenario(id: "preview-cloud-proposal")

    #expect(parallel?.task?.agents.count == 3)
    #expect(parallel?.task?.agents.allSatisfy { $0.id.hasPrefix("preview-") } == true)
    #expect(parallel?.task?.approvals.first?.state == .required)
    #expect(cloud?.task?.route == .cloudProposal)
    #expect(cloud?.task?.approvals.first?.allowedInteraction == .showNextPreviewState)
    #expect(ProductPreviewProvider.isRuntimeFallbackAllowed == false)
}

@Test func finalTaskWorkspaceMakesTheWholeExecutionStoryVisible() {
    let surface = PreviewWorkspaceSurfaceContract.productDefault

    #expect(surface.developmentLaunchArgument == "--product-preview")
    #expect(surface.productionDefaultsToRuntime == true)
    #expect(surface.disclosurePlacement == .persistentTopBanner)
    #expect(surface.sections == [
        .goalAndRoute,
        .executionRail,
        .parallelAgents,
        .approvalScope,
        .artifactsAndValidation,
        .resultAndUnresolvedEvidence,
    ])
    #expect(surface.runtimeActionsAllowed == false)
}

@Test func firstRunExplainsOneManagedProductInsteadOfFourDeployments() {
    let firstRun = FirstRunSurfaceContract.productDefault

    #expect(firstRun.developmentLaunchArgument == "--first-run-preview")
    #expect(firstRun.productionAppearsOnlyWhenOnboardingIsIncomplete == true)
    #expect(firstRun.steps == [
        .welcome,
        .privacy,
        .prepareLocalAI,
        .recommendedModel,
        .macOSPermissions,
        .optionalCloud,
        .createFirstTask,
    ])
    #expect(firstRun.localPreparationIsProductManaged == true)
    #expect(firstRun.requiresManualTerminalSetup == false)
    #expect(firstRun.exposesUpstreamProjectNamesToNovices == false)
    #expect(firstRun.languageSelection == .requiredBeforeOnboarding)
    #expect(firstRun.supportedLanguages == [.simplifiedChinese, .english])
}

@Test func dailyWorkbenchShowsTheBilingualPreTaskProductShape() {
    let surface = DailyWorkbenchSurfaceContract.productDefault

    #expect(surface.developmentLaunchArgument == "--daily-workbench-preview")
    #expect(surface.productionDefaultsToRuntime == true)
    #expect(surface.sections == [
        .primaryNavigation,
        .recentTasks,
        .newTaskComposer,
        .routeAndPrivacy,
        .contextAttachments,
        .supervisionRail,
    ])
    #expect(surface.supportedLanguages == [.simplifiedChinese, .english])
    #expect(surface.languageSwitchIsVisible == true)
    #expect(surface.supervisionRailIsCollapsible == true)
    #expect(surface.runtimeActionsAllowed == false)
    #expect(surface.readsAttachmentContents == false)
    #expect(surface.persistsPreviewHistory == false)
}

@Test func composeToExecutionPreviewHasOneDeterministicBilingualPath() {
    let transition = ComposeToExecutionPreviewContract.productDefault

    #expect(transition.stages == [
        .compose,
        .routeReview,
        .plan,
        .parallelExecution,
        .approval,
        .validation,
        .result,
    ])
    #expect(transition.supportedLanguages == [.simplifiedChinese, .english])
    #expect(transition.allowedInteraction == .showNextPreviewState)
    #expect(transition.languageSwitchPreservesStage == true)
    #expect(transition.runtimeActionsAllowed == false)
    #expect(transition.performsApproval == false)
    #expect(transition.persistsState == false)
}

@Test func historyRecoveryPreviewDistinguishesLifecycleTruthWithoutPerformingRecovery() {
    let history = HistoryRecoveryPreviewContract.productDefault

    #expect(history.states == [
        .interrupted,
        .blocked,
        .failed,
        .partial,
        .cancelled,
        .completed,
        .unknown,
    ])
    #expect(history.sections == [
        .taskList,
        .taskDetail,
        .executionSummary,
        .recoveryDecision,
        .auditBoundary,
    ])
    #expect(history.supportedLanguages == [.simplifiedChinese, .english])
    #expect(history.allowedInteraction == .showNextPreviewState)
    #expect(history.languageSwitchPreservesSelection == true)
    #expect(history.readsPersistedHistory == false)
    #expect(history.runtimeActionsAllowed == false)
    #expect(history.performsResume == false)
    #expect(history.performsRetry == false)
    #expect(history.performsCancellation == false)
    #expect(history.performsForceTermination == false)
}

@Test func governedMemoryReviewPreviewPresentsCandidateConflictCorrectionAndDeleteStates() {
    let memory = GovernedMemoryReviewContract.productDefault

    #expect(memory.states == [
        .candidate,
        .confirmed,
        .conflict,
        .correction,
        .deleted,
    ])
    #expect(memory.sections == [
        .recordList,
        .recordDetail,
        .provenance,
        .authorityBoundary,
    ])
    #expect(memory.supportedLanguages == [.simplifiedChinese, .english])
    #expect(memory.allowedInteraction == .showNextPreviewState)
    #expect(memory.languageSwitchPreservesSelection == true)
}

@Test func governedMemoryReviewPreviewIsReadOnlyAndBoundedBySemanticaAuthority() {
    let memory = GovernedMemoryReviewContract.productDefault

    #expect(memory.readsPersistentMemory == false)
    #expect(memory.runtimeActionsAllowed == false)
    #expect(memory.performsPromote == false)
    #expect(memory.performsCorrect == false)
    #expect(memory.performsDelete == false)
}

@Test func agentsToolsPreviewPresentsAdapterScopeWithoutReimplementation() {
    let agents = AgentsToolsContract.productDefault

    #expect(agents.agentKinds == [.herdrTerminal, .codexCompatible, .claudeCompatible, .holaOSReference])
    #expect(agents.requiredOperations == ["discover", "dispatch", "status", "handoff", "cancel", "resume", "artifacts", "audit"])
    #expect(agents.sections == [.agentList, .agentDetail, .requiredOperations, .authorityBoundary])
    #expect(agents.supportedLanguages == [.simplifiedChinese, .english])
    #expect(agents.allowedInteraction == .showNextPreviewState)
    #expect(agents.languageSwitchPreservesSelection == true)
    #expect(agents.runtimeActionsAllowed == false)
    #expect(agents.performsDispatch == false)
    #expect(agents.reimplementsUpstream == false)
}

@Test func permissionsPreviewPresentsScopesWithoutGrantingApproval() {
    let permissions = PermissionsContract.productDefault

    #expect(permissions.scopes == [.read, .write, .send, .delete, .execute, .credential])
    #expect(permissions.sections == [.scopeList, .scopeDetail, .approvalPolicy, .authorityBoundary])
    #expect(permissions.supportedLanguages == [.simplifiedChinese, .english])
    #expect(permissions.allowedInteraction == .showNextPreviewState)
    #expect(permissions.languageSwitchPreservesSelection == true)
    #expect(permissions.runtimeActionsAllowed == false)
    #expect(permissions.performsApproval == false)
    #expect(permissions.grantsPermission == false)
}

@Test func modelsProvidersPreviewIsLocalFirstWithoutModelDownload() {
    let models = ModelsProvidersContract.productDefault

    #expect(models.routeStates == [.automaticLocalFirst, .localOnly, .cloudWithApproval])
    #expect(models.supportedLanguages == [.simplifiedChinese, .english])
    #expect(models.allowedInteraction == .showNextPreviewState)
    #expect(models.runtimeActionsAllowed == false)
    #expect(models.downloadsModel == false)
    #expect(models.cloudDisabledByDefault == true)
}

@Test func localRuntimePreviewReportsHonestStateWithoutStartingRuntime() {
    let runtime = LocalRuntimeContract.productDefault

    #expect(runtime.states == [.stopped, .starting, .running, .degraded, .failed])
    #expect(runtime.supportedLanguages == [.simplifiedChinese, .english])
    #expect(runtime.allowedInteraction == .showNextPreviewState)
    #expect(runtime.runtimeActionsAllowed == false)
    #expect(runtime.startsRuntime == false)
    #expect(runtime.reportsHonestState == true)
}

@Test func dataPrivacyPreviewStoresSecretsInKeychainWithoutReadingUserData() {
    let privacy = DataPrivacyContract.productDefault

    #expect(privacy.supportedLanguages == [.simplifiedChinese, .english])
    #expect(privacy.allowedInteraction == .showNextPreviewState)
    #expect(privacy.runtimeActionsAllowed == false)
    #expect(privacy.storesSecretsInKeychain == true)
    #expect(privacy.readsUserData == false)
}

@Test func diagnosticsRecoveryPreviewDegradesHonestlyWithoutRecovery() {
    let diagnostics = DiagnosticsRecoveryContract.productDefault

    #expect(diagnostics.supportedLanguages == [.simplifiedChinese, .english])
    #expect(diagnostics.allowedInteraction == .showNextPreviewState)
    #expect(diagnostics.runtimeActionsAllowed == false)
    #expect(diagnostics.performsRecovery == false)
    #expect(diagnostics.honestDegradation == true)
}

@Test func governedMemoryReviewRealServiceBindingMapsSemanticaTruthFields() {
    let binding = GovernedMemoryReviewContract.realServiceBinding

    #expect(binding.loopbackPort == 43111)
    #expect(binding.auditPath == "logs/audit/memory-review.jsonl")
    #expect(binding.confirmedAuthority == "semantica")
    #expect(binding.snapshotCommand == "memory-review-snapshot")
    #expect(binding.confirmCommand == "memory-review-confirm")
    #expect(binding.rejectCommand == "memory-review-reject")
    #expect(binding.routes["confirm"]?.path == "/v1/memory/confirm")
    #expect(binding.uiStateFields[.confirmed]?.semanticaID == "semantica_id")
    #expect(GovernedMemoryReviewContract.productDefault.readsPersistentMemory == false)
    #expect(GovernedMemoryReviewContract.productDefault.runtimeActionsAllowed == false)
}

@Test func taskMetadataProjectionIsBoundedByHerdrAuthority() {
    let projection = HistoryRecoveryPreviewContract.metadataProjection

    #expect(projection.runtimeAuthority == "herdr")
    #expect(projection.forbiddenMetadataClaims.contains("completed"))
    #expect(projection.forbiddenMetadataClaims.contains("resumable"))
    #expect(projection.productOwnedFields.contains("task_id"))
    #expect(HistoryRecoveryPreviewContract.productDefault.readsPersistedHistory == false)
    #expect(HistoryRecoveryPreviewContract.productDefault.performsResume == false)
}

@Test func taskMetadataPersistenceDoesNotClaimRuntimeAuthority() {
    let persistence = HistoryRecoveryPreviewContract.metadataPersistence

    #expect(persistence.persistsRuntimeClaims == false)
    #expect(persistence.storageRelativeDirectory == "state/task-metadata")
    #expect(persistence.recordSchemaVersion == 1)
    #expect(persistence.productOwnedFields.contains("last_accepted_revision"))
    #expect(persistence.productOwnedFields.contains("approval_refs"))
}

