import SwiftUI
import LifecycleContract

struct FirstRunPreview: View {
    private let contract = FirstRunSurfaceContract.productDefault
    @State private var selectedStep: FirstRunStep = .welcome

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Label("Product Preview · synthetic data · no runtime action", systemImage: "eye.trianglebadge.exclamationmark")
                    .font(.callout.weight(.semibold))
                Spacer()
            }
            .padding(.horizontal, 20).padding(.vertical, 10)
            .background(Color(red: 0.96, green: 0.76, blue: 0.22))
            .foregroundStyle(.black.opacity(0.78))

            HStack(spacing: 0) {
                VStack(alignment: .leading, spacing: 28) {
                    VStack(alignment: .leading, spacing: 8) {
                        Image(systemName: "sparkles.rectangle.stack.fill")
                            .font(.system(size: 30)).foregroundStyle(.blue)
                        Text("Forma AI").font(.title2.weight(.bold))
                        Text("Your private, local-first AI workbench")
                            .font(.callout).foregroundStyle(.secondary)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(Array(contract.steps.enumerated()), id: \.element) { index, step in
                            Button { selectedStep = step } label: {
                                HStack(spacing: 12) {
                                    Text("\(index + 1)").font(.caption.monospaced().weight(.bold))
                                        .frame(width: 24, height: 24)
                                        .background(selectedStep == step ? Color.blue : Color.secondary.opacity(0.13), in: Circle())
                                        .foregroundStyle(selectedStep == step ? .white : .secondary)
                                    Text(step.title).font(.callout.weight(selectedStep == step ? .semibold : .regular))
                                    Spacer()
                                }
                                .padding(.vertical, 8).padding(.horizontal, 10)
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    Spacer()
                    Text("Preview navigation only").font(.caption).foregroundStyle(.tertiary)
                }
                .padding(30).frame(width: 300).background(.thinMaterial)

                Divider()

                VStack(alignment: .leading, spacing: 26) {
                    Spacer()
                    Text(selectedStep.eyebrow.uppercased())
                        .font(.caption.monospaced().weight(.bold)).foregroundStyle(.blue)
                    Text(selectedStep.headline)
                        .font(.system(size: 36, weight: .semibold, design: .rounded))
                        .frame(maxWidth: 650, alignment: .leading)
                    Text(selectedStep.explanation)
                        .font(.title3).foregroundStyle(.secondary)
                        .frame(maxWidth: 650, alignment: .leading)
                    preparationMap
                    Spacer()
                    HStack {
                        Text("Nothing is downloaded, installed, or sent in Product Preview.")
                            .font(.caption).foregroundStyle(.secondary)
                        Spacer()
                        Button(selectedStep == .createFirstTask ? "Create first task" : "Continue") {
                            advance()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding(44).frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .frame(minWidth: 980, minHeight: 650)
    }

    private var preparationMap: some View {
        HStack(spacing: 12) {
            readinessCard("Private by default", "lock.shield.fill", .green)
            readinessCard("Local AI managed for you", "laptopcomputer.and.arrow.down", .blue)
            readinessCard("Cloud stays optional", "cloud", .orange)
        }
        .frame(maxWidth: 720)
    }

    private func readinessCard(_ title: String, _ symbol: String, _ color: Color) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Image(systemName: symbol).font(.title2).foregroundStyle(color)
            Text(title).font(.headline)
        }
        .padding(16).frame(maxWidth: .infinity, minHeight: 110, alignment: .topLeading)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 15))
        .overlay(RoundedRectangle(cornerRadius: 15).stroke(.separator.opacity(0.5)))
    }

    private func advance() {
        guard let index = contract.steps.firstIndex(of: selectedStep), index + 1 < contract.steps.count else { return }
        selectedStep = contract.steps[index + 1]
    }
}

private extension FirstRunStep {
    var title: String {
        switch self {
        case .welcome: "Welcome"
        case .privacy: "Privacy"
        case .prepareLocalAI: "Prepare local AI"
        case .recommendedModel: "Recommended model"
        case .macOSPermissions: "macOS permissions"
        case .optionalCloud: "Optional cloud"
        case .createFirstTask: "First task"
        }
    }

    var eyebrow: String { self == .welcome ? "Welcome" : "Step \(FirstRunStep.allCases.firstIndex(of: self)! + 1) of 7" }

    var headline: String {
        switch self {
        case .welcome: "One application for private, supervised AI work."
        case .privacy: "Your work stays on this Mac unless you approve otherwise."
        case .prepareLocalAI: "Forma AI prepares local intelligence automatically."
        case .recommendedModel: "Start with the model that fits this Mac."
        case .macOSPermissions: "Grant only the access each task genuinely needs."
        case .optionalCloud: "Cloud models are optional and always ask first."
        case .createFirstTask: "You are ready to create your first task."
        }
    }

    var explanation: String {
        switch self {
        case .welcome: "Plan work, supervise parallel agents, review approvals, and keep evidence together in one native workbench."
        case .privacy: "Local routes are preferred. Before any cloud transmission or external write, you see the exact scope and decide."
        case .prepareLocalAI: "The product manages compatible local capabilities, versions, startup, repair, and removal. No separate setup is required."
        case .recommendedModel: "Forma AI recommends a balanced local profile from this Mac’s available memory and performance. You can change it later."
        case .macOSPermissions: "Permissions are requested progressively, at the moment a real task needs them—not as a blanket first-launch demand."
        case .optionalCloud: "Add a provider only if you want one. Credentials remain protected, and every transmission still requires review."
        case .createFirstTask: "Describe an outcome in plain language. Forma AI will propose a safe route and show how the work is divided."
        }
    }
}
