//
//  QuizViewModel.swift
//  G1 test
//
//  Owns the state and logic of a single quiz session: question order,
//  shuffled answer choices, the current selection, scoring, and recording
//  mistakes. Keeping this out of the View makes the flow easy to reason
//  about and test.
//

import Foundation
import Observation

@Observable
final class QuizViewModel {

    /// A single answer option, with a stable identity for SwiftUI and a
    /// pre-computed `isCorrect` flag so the view never needs the original index.
    struct Choice: Identifiable, Equatable {
        let id = UUID()
        let text: String
        let isCorrect: Bool
    }

    let title: String
    let language: AppLanguage

    private(set) var questions: [Question]
    private var choicesByQuestion: [String: [Choice]] = [:]

    private(set) var currentIndex = 0
    private(set) var selectedChoiceID: UUID?
    private(set) var isAnswered = false
    private(set) var correctCount = 0
    var showResults = false
    /// True once the last question has been answered and results were shown.
    /// Cleared by `restart()`, so a finished set always starts fresh.
    private(set) var isFinished = false

    private let mistakes: MistakesStore

    init(title: String, language: AppLanguage, questions: [Question], mistakes: MistakesStore) {
        self.title = title
        self.language = language
        self.questions = questions.shuffled()
        self.mistakes = mistakes
        rebuildChoices()
    }

    // MARK: - Derived state

    var isEmpty: Bool { questions.isEmpty }
    var total: Int { questions.count }

    var currentQuestion: Question? {
        questions.indices.contains(currentIndex) ? questions[currentIndex] : nil
    }

    var currentChoices: [Choice] {
        guard let q = currentQuestion else { return [] }
        return choicesByQuestion[q.id] ?? []
    }

    var isLastQuestion: Bool { currentIndex >= questions.count - 1 }

    var progressValue: Double {
        guard !questions.isEmpty else { return 0 }
        return Double(currentIndex + 1) / Double(questions.count)
    }

    // MARK: - Actions

    /// Records the user's answer for the current question (once).
    func select(_ choice: Choice) {
        guard !isAnswered, let q = currentQuestion else { return }
        selectedChoiceID = choice.id
        isAnswered = true
        if choice.isCorrect {
            correctCount += 1
            mistakes.clear(q.id)        // a corrected mistake leaves the list
        } else {
            mistakes.record(q.id)
        }
    }

    /// Advances to the next question, or shows results if finished.
    func advance() {
        if isLastQuestion {
            isFinished = true
            showResults = true
        } else {
            currentIndex += 1
            selectedChoiceID = nil
            isAnswered = false
        }
    }

    /// Restarts the same set with freshly shuffled questions and choices.
    func restart() {
        questions.shuffle()
        rebuildChoices()
        currentIndex = 0
        selectedChoiceID = nil
        isAnswered = false
        correctCount = 0
        isFinished = false
        showResults = false
    }

    // MARK: - Helpers

    private func rebuildChoices() {
        choicesByQuestion = Dictionary(
            uniqueKeysWithValues: questions.map { ($0.id, Self.makeChoices(for: $0)) }
        )
    }

    private static func makeChoices(for q: Question) -> [Choice] {
        q.options.enumerated()
            .map { Choice(text: $0.element, isCorrect: $0.offset == q.correctIndex) }
            .shuffled()
    }
}
