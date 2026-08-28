//
//  Models.swift
//  G1 test
//
//  Core domain models for the G1 practice app.
//  Questions are loaded from `questions.json` (see QuestionBank).
//

import Foundation

/// The languages the app supports. The raw value matches the `language`
/// field in questions.json ("en" / "fa").
enum AppLanguage: String, Codable, CaseIterable, Identifiable {
    case english = "en"
    case persian = "fa"

    var id: String { rawValue }

    /// Label shown on the language-selection buttons.
    var displayName: String {
        switch self {
        case .english: return "ENGLISH"
        case .persian: return "فارسی"
        }
    }

    /// Persian reads right-to-left; used to flip layout direction.
    var isRightToLeft: Bool { self == .persian }
}

/// A question is either about road *signs* (has an image) or *rules* (text only).
enum QuestionCategory: String, Codable {
    case signs
    case rules
}

/// A single quiz question. Immutable value type decoded from JSON.
struct Question: Identifiable, Codable, Hashable {
    let id: String              // e.g. "en-3", "fa-201" — unique across the app
    let language: AppLanguage
    let category: QuestionCategory
    let test: Int               // which test (1-based) this question belongs to
    let text: String
    let options: [String]       // answer choices in their original order
    let correctIndex: Int       // index into `options` of the correct answer
    let imageName: String?      // asset name for sign questions; nil for rules

    /// The correct answer text. Falls back to "" if data is malformed.
    var correctOption: String {
        options.indices.contains(correctIndex) ? options[correctIndex] : ""
    }

    /// Whether a usable image asset exists in the bundle for this question.
    var hasImage: Bool {
        guard let name = imageName, !name.isEmpty else { return false }
        return ImageAvailability.exists(name)
    }
}
