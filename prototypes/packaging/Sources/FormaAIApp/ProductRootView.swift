import SwiftUI
import LifecycleContract

struct ProductRootView: View {
    @State private var showWorkbench = OnboardingPreferences.isComplete

    var body: some View {
        Group {
            if showWorkbench {
                DailyWorkbenchShell(presentation: .production)
            } else {
                FirstRunProductionFlow {
                    showWorkbench = true
                }
            }
        }
    }
}
