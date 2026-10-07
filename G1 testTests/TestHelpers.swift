//
//  TestHelpers.swift
//  G1 testTests
//
//  Small factories shared by the unit tests.
//

import Foundation
@testable import G1_test

enum TestData {
    /// A hand-made question; the correct answer is always "Correct \(n)".
    static func question(
        _ n: Int,
        language: AppLanguage = .english,
        category: QuestionCategory = .rules,
        test: Int = 1,
        correctIndex: Int = 0,
        imageName: String? = nil
    ) -> Question {
        var options = ["Wrong A \(n)", "Wrong B \(n)", "Wrong C \(n)"]
        options.insert("Correct \(n)", at: min(max(correctIndex, 0), options.count))
        return Question(
            id: "\(language.rawValue)-\(n)",
            language: language,
            category: category,
            test: test,
            text: "Question \(n)?",
            options: options,
            correctIndex: correctIndex,
            imageName: imageName
        )
    }

    static func questions(_ count: Int, language: AppLanguage = .english) -> [Question] {
        (1...max(count, 1)).prefix(count).map { question($0, language: language, correctIndex: $0 % 4) }
    }

    /// A MistakesStore backed by its own throw-away UserDefaults suite, so
    /// tests never touch (or depend on) the real app data or each other.
    static func isolatedMistakes() -> (MistakesStore, UserDefaults) {
        let suite = "G1Tests-\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suite)!
        defaults.removePersistentDomain(forName: suite)
        return (MistakesStore(defaults: defaults), defaults)
    }
}
