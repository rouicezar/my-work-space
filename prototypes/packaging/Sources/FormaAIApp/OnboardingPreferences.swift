import Foundation
import LifecycleContract

enum OnboardingPreferences {
    static let completedKey = "forma.product.onboarding.completed"
    static let languageKey = "forma.product.language"
    static let sidebarWidthKey = "forma.product.sidebar.width"
    static let supervisionWidthKey = "forma.product.supervision.width"

    static var isComplete: Bool {
        UserDefaults.standard.bool(forKey: completedKey)
    }

    static var storedLanguage: ProductLanguage {
        let raw = UserDefaults.standard.string(forKey: languageKey) ?? ProductLanguage.simplifiedChinese.rawValue
        return ProductLanguage(rawValue: raw) ?? .simplifiedChinese
    }

    static func markComplete(language: ProductLanguage) {
        UserDefaults.standard.set(true, forKey: completedKey)
        UserDefaults.standard.set(language.rawValue, forKey: languageKey)
    }

    static func resetForTesting() {
        UserDefaults.standard.removeObject(forKey: completedKey)
    }
}
