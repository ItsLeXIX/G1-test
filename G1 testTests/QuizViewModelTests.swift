//
//  QuizViewModelTests.swift
//  G1 testTests
//
//  The quiz flow: shuffling, answering, scoring, mistakes, finishing and
//  restarting (including the "Done resets the set" fix).
//

import Foundation
import Testing
@testable import G1_test

@Suite("QuizViewModel")
struct QuizViewModelTests {

    private func makeVM(_ questions: [Question],
                        language: AppLanguage = .english) -> (QuizViewModel, MistakesStore) {
        let (store, _) = TestData.isolatedMistakes()
        let vm = QuizViewModel(title: "Test", language: language, questions: questions, mistakes: store)
        return (vm, store)
    }

    private func correctChoice(_ vm: QuizViewModel) throws -> QuizViewModel.Choice {
        try #require(vm.currentChoices.first(where: \.isCorrect))
    }

    private func wrongChoice(_ vm: QuizViewModel) throws -> QuizViewModel.Choice {
        try #require(vm.currentChoices.first(where: { !$0.isCorrect }))
    }

    /// Answers every question (correctly or not) and presses Next/Finish.
    private func playThrough(_ vm: QuizViewModel, correct: Bool) throws {
        for _ in 0..<vm.total {
            if correct { vm.select(try correctChoice(vm)) } else { vm.select(try wrongChoice(vm)) }
            vm.advance()
        }
    }

    // MARK: Initial state

    @Test func initialState() throws {
        let (vm, _) = makeVM(TestData.questions(5))
        #expect(vm.title == "Test")
        #expect(vm.language == .english)
        #expect(vm.total == 5)
        #expect(!vm.isEmpty)
        #expect(vm.currentIndex == 0)
        #expect(vm.selectedChoiceID == nil)
        #expect(!vm.isAnswered)
        #expect(vm.correctCount == 0)
        #expect(!vm.showResults)
        #expect(!vm.isFinished)
        #expect(vm.currentQuestion != nil)
    }

    @Test func keepsTheSameQuestionsWhenShuffling() {
        let input = TestData.questions(10)
        let (vm, _) = makeVM(input)
        #expect(Set(vm.questions.map(\.id)) == Set(input.map(\.id)))
        #expect(vm.questions.count == input.count)
    }

    @Test func emptyQuiz() {
        let (vm, _) = makeVM([])
        #expect(vm.isEmpty)
        #expect(vm.total == 0)
        #expect(vm.currentQuestion == nil)
        #expect(vm.currentChoices.isEmpty)
        #expect(vm.progressValue == 0)
    }

    // MARK: Choices

    @Test func everyQuestionHasFourChoicesWithExactlyOneCorrect() throws {
        let (vm, _) = makeVM(TestData.questions(4))
        for _ in 0..<vm.total {
            let q = try #require(vm.currentQuestion)
            let choices = vm.currentChoices
            #expect(choices.count == 4)
            #expect(choices.filter(\.isCorrect).count == 1)
            #expect(Set(choices.map(\.text)) == Set(q.options))
            #expect(choices.first(where: \.isCorrect)?.text == q.correctOption)
            vm.select(choices[0])
            vm.advance()
        }
    }

    @Test func choicesAreStableBetweenReads() {
        let (vm, _) = makeVM(TestData.questions(3))
        #expect(vm.currentChoices.map(\.id) == vm.currentChoices.map(\.id))
    }

    @Test func choicesWorkForRealQuestionsInBothLanguages() throws {
        for language in AppLanguage.allCases {
            let real = QuestionBank.questions(language: language, test: 1)
            let (vm, _) = makeVM(real, language: language)
            let q = try #require(vm.currentQuestion)
            #expect(vm.currentChoices.first(where: \.isCorrect)?.text == q.correctOption)
        }
    }

    // MARK: Answering

    @Test func selectingCorrectAnswerScores() throws {
        let (vm, store) = makeVM(TestData.questions(3))
        let choice = try correctChoice(vm)
        vm.select(choice)
        #expect(vm.isAnswered)
        #expect(vm.selectedChoiceID == choice.id)
        #expect(vm.correctCount == 1)
        #expect(store.missedIDs.isEmpty)
    }

    @Test func selectingWrongAnswerRecordsMistake() throws {
        let (vm, store) = makeVM(TestData.questions(3))
        let q = try #require(vm.currentQuestion)
        vm.select(try wrongChoice(vm))
        #expect(vm.isAnswered)
        #expect(vm.correctCount == 0)
        #expect(store.missedIDs == [q.id])
    }

    @Test func correctAnswerClearsAnEarlierMistake() throws {
        let (store, _) = TestData.isolatedMistakes()
        let q = TestData.question(1)
        store.record(q.id)
        let vm = QuizViewModel(title: "Mistakes", language: .english, questions: [q], mistakes: store)
        vm.select(try correctChoice(vm))
        #expect(store.missedIDs.isEmpty)
    }

    @Test func onlyTheFirstAnswerCounts() throws {
        let (vm, store) = makeVM(TestData.questions(3))
        let wrong = try wrongChoice(vm)
        vm.select(wrong)
        vm.select(try correctChoice(vm))          // ignored
        #expect(vm.selectedChoiceID == wrong.id)
        #expect(vm.correctCount == 0)
        #expect(store.missedIDs.count == 1)
    }

    // MARK: Moving through the set

    @Test func advanceMovesToNextQuestionAndClearsSelection() throws {
        let (vm, _) = makeVM(TestData.questions(3))
        let first = vm.currentQuestion?.id
        vm.select(try correctChoice(vm))
        vm.advance()
        #expect(vm.currentIndex == 1)
        #expect(vm.currentQuestion?.id != first)
        #expect(vm.selectedChoiceID == nil)
        #expect(!vm.isAnswered)
        #expect(!vm.showResults)
        #expect(!vm.isFinished)
    }

    @Test func progressValueTracksPosition() throws {
        let (vm, _) = makeVM(TestData.questions(4))
        #expect(vm.progressValue == 0.25)
        vm.select(try correctChoice(vm)); vm.advance()
        #expect(vm.progressValue == 0.5)
    }

    @Test func isLastQuestionOnlyOnTheLastOne() throws {
        let (vm, _) = makeVM(TestData.questions(3))
        #expect(!vm.isLastQuestion)
        vm.select(try correctChoice(vm)); vm.advance()
        #expect(!vm.isLastQuestion)
        vm.select(try correctChoice(vm)); vm.advance()
        #expect(vm.isLastQuestion)
    }

    @Test func singleQuestionIsAlsoTheLast() {
        let (vm, _) = makeVM(TestData.questions(1))
        #expect(vm.isLastQuestion)
    }

    // MARK: Finishing

    @Test func finishingShowsResultsAndMarksFinished() throws {
        let (vm, _) = makeVM(TestData.questions(3))
        try playThrough(vm, correct: true)
        #expect(vm.showResults)
        #expect(vm.isFinished)
        #expect(vm.currentIndex == 2)          // stays on the last question
    }

    @Test func perfectRunScoresEveryQuestion() throws {
        let (vm, store) = makeVM(TestData.questions(5))
        try playThrough(vm, correct: true)
        #expect(vm.correctCount == 5)
        #expect(store.missedIDs.isEmpty)
    }

    @Test func allWrongRunRecordsEveryQuestion() throws {
        let input = TestData.questions(5)
        let (vm, store) = makeVM(input)
        try playThrough(vm, correct: false)
        #expect(vm.correctCount == 0)
        #expect(store.missedIDs == Set(input.map(\.id)))
    }

    // MARK: Restarting ("Try again" and "Done")

    @Test func restartResetsEverything() throws {
        let input = TestData.questions(4)
        let (vm, _) = makeVM(input)
        try playThrough(vm, correct: true)

        vm.restart()
        #expect(vm.currentIndex == 0)
        #expect(vm.selectedChoiceID == nil)
        #expect(!vm.isAnswered)
        #expect(vm.correctCount == 0)
        #expect(!vm.showResults)
        #expect(!vm.isFinished)
        #expect(Set(vm.questions.map(\.id)) == Set(input.map(\.id)))
    }

    @Test func restartedSetCanBePlayedAgain() throws {
        let (vm, _) = makeVM(TestData.questions(3))
        try playThrough(vm, correct: false)
        vm.restart()
        try playThrough(vm, correct: true)
        #expect(vm.correctCount == 3)          // old score does not carry over
        #expect(vm.isFinished)
    }

    @Test func restartRebuildsChoicesForEveryQuestion() throws {
        let (vm, _) = makeVM(TestData.questions(4))
        try playThrough(vm, correct: true)
        vm.restart()
        for _ in 0..<vm.total {
            #expect(vm.currentChoices.count == 4)
            #expect(vm.currentChoices.filter(\.isCorrect).count == 1)
            vm.select(try correctChoice(vm)); vm.advance()
        }
    }

    @Test func leavingMidSetKeepsProgress() throws {
        // Pressing Back mid-set must NOT reset (only finishing does).
        let (vm, _) = makeVM(TestData.questions(5))
        vm.select(try correctChoice(vm)); vm.advance()
        vm.select(try correctChoice(vm)); vm.advance()
        #expect(!vm.isFinished)
        #expect(vm.currentIndex == 2)
        #expect(vm.correctCount == 2)
    }
}
