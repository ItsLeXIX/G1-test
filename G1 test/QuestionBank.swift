//
//  QuestionBank.swift
//  G1 test
//
//  Loads the question bank from the bundled questions.json and provides
//  simple, read-only queries. Questions are static data, so this is a
//  lightweight replacement for the previous Core Data store + seeder.
//

import Foundation
import UIKit

/// Checks whether an image asset is present in the app bundle.
enum ImageAvailability {
    static func exists(_ name: String) -> Bool {
        UIImage(named: name) != nil
    }
}

enum QuestionBank {
    /// All questions, loaded once and cached.
    static let all: [Question] = load()

    /// Distinct test numbers available for a language, in order.
    static func tests(for language: AppLanguage) -> [Int] {
        Set(all.filter { $0.language == language }.map(\.test)).sorted()
    }

    /// Questions for a specific language + test, sorted by id for stable order.
    static func questions(language: AppLanguage, test: Int) -> [Question] {
        all.filter { $0.language == language && $0.test == test }
            .sorted { $0.id < $1.id }
    }

    /// A random selection across all tests of a language (a "mock exam").
    static func mockTest(language: AppLanguage, count: Int = 20) -> [Question] {
        Array(all.filter { $0.language == language }.shuffled().prefix(count))
    }

    /// Questions matching a set of ids, restricted to one language.
    static func questions(ids: Set<String>, language: AppLanguage) -> [Question] {
        all.filter { $0.language == language && ids.contains($0.id) }
            .sorted { $0.id < $1.id }
    }

    // MARK: - Loading

    private struct QuestionFile: Codable { let questions: [Question] }

    private static func load() -> [Question] {
        guard let url = Bundle.main.url(forResource: "questions", withExtension: "json") else {
            assertionFailure("questions.json is missing from the app bundle.")
            return []
        }
        do {
            let data = try Data(contentsOf: url)
            return try JSONDecoder().decode(QuestionFile.self, from: data).questions
        } catch {
            assertionFailure("Failed to load questions.json: \(error)")
            return []
        }
    }
}
