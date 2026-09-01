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
