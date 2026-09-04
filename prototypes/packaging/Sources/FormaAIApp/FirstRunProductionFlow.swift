import SwiftUI
import LifecycleContract

struct FirstRunProductionFlow: View {
    @State private var language: ProductLanguage?
    @StateObject private var preparation = LocalAIPreparationCoordinator()
    let onComplete: () -> Void

    var body: some View {
        Group {
            if let language {
                FirstRunAssistantView(
                    mode: .production,
                    language: language,
                    preparation: preparation,
                    onChangeLanguage: { self.language = nil },
                    onComplete: onComplete
                )
            } else {
                languageSelection
            }
        }
    }

    private var languageSelection: some View {
        VStack(spacing: 28) {
            Spacer()
            Image(systemName: "sparkles.rectangle.stack.fill")
                .font(.system(size: 48)).foregroundStyle(.blue)
            VStack(spacing: 10) {
                Text("欢迎使用 Forma AI").font(.system(size: 34, weight: .semibold, design: .rounded))
                Text("Welcome to Forma AI").font(.title2.weight(.medium))
                Text("请选择语言 · Choose your language")
                    .font(.title3).foregroundStyle(.secondary)
            }
            HStack(spacing: 18) {
                languageButton(.simplifiedChinese, title: "简体中文", subtitle: "继续使用中文")
                languageButton(.english, title: "English", subtitle: "Continue in English")
            }
            .frame(maxWidth: 640)
            Text("稍后可在设置中更改 · You can change this later in Settings")
                .font(.caption).foregroundStyle(.secondary)
            Spacer()
        }
        .padding(44).frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func languageButton(_ value: ProductLanguage, title: String, subtitle: String) -> some View {
        Button {
            language = value
            UserDefaults.standard.set(value.rawValue, forKey: OnboardingPreferences.languageKey)
        } label: {
            VStack(alignment: .leading, spacing: 10) {
                Image(systemName: "character.bubble.fill").font(.title2).foregroundStyle(.blue)
                Text(title).font(.title3.weight(.semibold))
                Text(subtitle).font(.callout).foregroundStyle(.secondary)
            }
            .padding(20).frame(maxWidth: .infinity, minHeight: 140, alignment: .topLeading)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(.blue.opacity(0.35), lineWidth: 1.5))
        }
        .buttonStyle(.plain)
    }
}
