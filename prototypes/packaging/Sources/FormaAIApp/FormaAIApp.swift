import SwiftUI
import LifecycleContract
import SupervisorProtocol
import RuntimeSecurity

@main
struct FormaAIPrototypeApp: App {
    var body: some Scene {
        WindowGroup("Forma AI") {
            Group {
#if DEBUG
                if CommandLine.arguments.contains(FirstRunSurfaceContract.productDefault.developmentLaunchArgument) {
                    FirstRunPreview()
                } else if CommandLine.arguments.contains(DailyWorkbenchSurfaceContract.productDefault.developmentLaunchArgument) {
                    DailyWorkbenchPreview()
                } else if CommandLine.arguments.contains(PreviewWorkspaceSurfaceContract.productDefault.developmentLaunchArgument) {
                    ProductPreviewWorkspace()
                } else if CommandLine.arguments.contains("--force-workbench") {
                    DailyWorkbenchShell(presentation: .production)
                } else {
                    ProductRootView()
                }
#else
                ProductRootView()
#endif
            }
                .frame(
                    minWidth: 980,
                    idealWidth: 1120,
                    minHeight: 620,
                    idealHeight: 760
                )
        }
    }
}

#if DEBUG
struct ParallelAgentWorkbenchPreview: PreviewProvider {
    static var previews: some View {
        DailyWorkbenchShell(presentation: .production, agentActivityFixture: RuntimePresentationState(
            freshness: "fresh",
            reason: nil,
            agents: [
                RuntimePresentedAgent(
                    paneID: "pane-001", terminalID: "terminal-001",
                    workspaceID: "workspace-001", tabID: "tab-001",
                    state: "working", revision: 1
                ),
            ]
        ))
    }
}
#endif
