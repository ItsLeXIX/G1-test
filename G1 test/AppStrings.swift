//
//  AppStrings.swift
//  G1 test
//
//  Centralized UI text for the in-app language toggle. Because the user
//  picks the language inside the app (rather than relying on the device
//  locale), the strings are keyed on `AppLanguage` here instead of using
//  a .strings/String Catalog file.
//

import Foundation

struct AppStrings {
    let language: AppLanguage

    private var isFa: Bool { language == .persian }

    // MARK: Welcome
    var welcomeTitle: String { isFa ? "آزمون تمرینی جی-۱" : "G1 Practice Test" }
    var selectLanguage: String { isFa ? "لطفاً زبان خود را انتخاب کنید" : "Please select your language" }

    // MARK: Menu
    var selectTest: String { isFa ? "یک آزمون را انتخاب کنید" : "Select a Test" }
    var mockTest: String { isFa ? "آزمون آزمایشی" : "Mock Test" }
    var mistakes: String { isFa ? "اشتباه‌ها" : "Mistakes" }

    func testTitle(_ number: Int) -> String {
        isFa ? "تست \(localizedNumber(number))" : "Test \(number)"
    }

    // MARK: Quiz
    var next: String { isFa ? "بعدی" : "Next" }
    var finish: String { isFa ? "پایان" : "Finish" }
    var results: String { isFa ? "نتیجه" : "Results" }
    var tryAgain: String { isFa ? "تلاش دوباره" : "Try Again" }
    var done: String { isFa ? "بستن" : "Done" }

    func progress(_ current: Int, _ total: Int) -> String {
        isFa ? "\(localizedNumber(current)) از \(localizedNumber(total))"
             : "\(current) of \(total)"
    }

    /// Empty-state message for the Mistakes list.
    var noMistakes: String {
        isFa ? "هنوز اشتباهی نداری. آفرین!" : "No mistakes yet. Nice work!"
    }

    var emptyTest: String {
        isFa ? "سؤالی برای این آزمون موجود نیست." : "No questions available for this test."
    }

    /// Encouraging feedback based on the final score.
    func feedback(score: Int, total: Int) -> String {
        guard total > 0 else { return "" }
        let pct = Double(score) / Double(total)
        switch pct {
        case 0.9...:
            return isFa ? "عالی بود!" : "Excellent work!"
        case 0.7..<0.9:
            return isFa ? "آفرین، تقریباً کامل." : "Nice job — almost perfect."
        case 0.5..<0.7:
            return isFa ? "ادامه بده، نزدیکی." : "Keep practicing — you're close."
        default:
            return isFa ? "یک بار دیگر امتحان کن." : "Give it another go!"
        }
    }

    // MARK: Helpers

    /// Converts Western digits to Persian digits for display.
    func localizedNumber(_ value: Int) -> String {
        guard isFa else { return String(value) }
        let map: [Character: Character] = [
            "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
            "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹"
        ]
        return String(String(value).map { map[$0] ?? $0 })
    }
}
