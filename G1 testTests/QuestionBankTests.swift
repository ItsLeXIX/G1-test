//
//  QuestionBankTests.swift
//  G1 testTests
//
//  Behaviour of the QuestionBank queries (loading, filtering, ordering).
//

import Testing
@testable import G1_test

@Suite("QuestionBank")
struct QuestionBankTests {

    @Test func questionsJSONLoads() {
        #expect(!QuestionBank.all.isEmpty)
    }

    @Test(arguments: AppLanguage.allCases)
    func testNumbersAreSortedAndUnique(language: AppLanguage) {
        let tests = QuestionBank.tests(for: language)
        #expect(!tests.isEmpty)
        #expect(tests == tests.sorted())
        #expect(Set(tests).count == tests.count)
    }

    @Test(arguments: AppLanguage.allCases)
    func testNumbersAreContiguousFromOne(language: AppLanguage) {
        let tests = QuestionBank.tests(for: language)
        #expect(tests == Array(1...(tests.last ?? 0)))
    }

    @Test func bothLanguagesHaveTheSameTests() {
        #expect(QuestionBank.tests(for: .english) == QuestionBank.tests(for: .persian))
    }

    @Test func questionsForTestAreFilteredByLanguageAndTest() {
        let qs = QuestionBank.questions(language: .persian, test: 3)
        #expect(!qs.isEmpty)
        #expect(qs.allSatisfy { $0.language == .persian && $0.test == 3 })
    }

    @Test func questionsForUnknownTestAreEmpty() {
        #expect(QuestionBank.questions(language: .english, test: 9_999).isEmpty)
    }

    @Test func questionsAreSortedByIDNumberNotText() {
        // Test 5 runs fa-181 ... fa-200. Sorting the ids as plain text would
        // put "fa-200" first; the bank must sort by the number.
        let ids = QuestionBank.questions(language: .persian, test: 5).map(\.id)
        #expect(ids.first == "fa-181")
        #expect(ids.last == "fa-200")
        let numbers = ids.compactMap { Int($0.split(separator: "-").last!) }
        #expect(numbers == numbers.sorted())
    }

    @Test(arguments: AppLanguage.allCases)
    func mockTestHasTwentyUniqueQuestionsInOneLanguage(language: AppLanguage) {
        let mock = QuestionBank.mockTest(language: language)
        #expect(mock.count == 20)
        #expect(Set(mock.map(\.id)).count == 20)
        #expect(mock.allSatisfy { $0.language == language })
    }

    @Test func mockTestRespectsCount() {
        #expect(QuestionBank.mockTest(language: .english, count: 5).count == 5)
        #expect(QuestionBank.mockTest(language: .english, count: 0).isEmpty)
    }

    @Test func mockTestNeverExceedsAvailableQuestions() {
        let available = QuestionBank.all.filter { $0.language == .english }.count
        #expect(QuestionBank.mockTest(language: .english, count: available + 100).count == available)
    }

    @Test func questionsByIDsReturnsOnlyMatchingLanguage() {
        let ids: Set<String> = ["en-101", "en-102", "fa-101"]
        let english = QuestionBank.questions(ids: ids, language: .english)
        #expect(english.map(\.id) == ["en-101", "en-102"])
        let persian = QuestionBank.questions(ids: ids, language: .persian)
        #expect(persian.map(\.id) == ["fa-101"])
    }

    @Test func questionsByIDsIgnoresUnknownIDs() {
        #expect(QuestionBank.questions(ids: ["en-0", "nope"], language: .english).isEmpty)
        #expect(QuestionBank.questions(ids: [], language: .english).isEmpty)
    }

    @Test func questionsByIDsAreSortedNumerically() {
        let ids: Set<String> = ["en-200", "en-181", "en-190"]
        #expect(QuestionBank.questions(ids: ids, language: .english).map(\.id)
                == ["en-181", "en-190", "en-200"])
    }

    @Test func imageAvailabilityChecksTheBundle() {
        #expect(ImageAvailability.exists("1"))
        #expect(ImageAvailability.exists("welcomeImage"))
        #expect(!ImageAvailability.exists("no-such-image-xyz"))
    }
}
