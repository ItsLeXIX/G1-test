//
//  AppStringsTests.swift
//  G1 testTests
//

import Testing
@testable import G1_test

@Suite("AppStrings")
struct AppStringsTests {
    let en = AppStrings(language: .english)
    let fa = AppStrings(language: .persian)

    // MARK: Numbers

    @Test func englishNumbersAreUnchanged() {
        #expect(en.localizedNumber(0) == "0")
        #expect(en.localizedNumber(1234567890) == "1234567890")
    }

    @Test func persianNumbersUsePersianDigits() {
        #expect(fa.localizedNumber(0) == "۰")
        #expect(fa.localizedNumber(1234567890) == "۱۲۳۴۵۶۷۸۹۰")
        #expect(fa.localizedNumber(20) == "۲۰")
    }

    @Test func persianNegativeNumberKeepsSign() {
        #expect(fa.localizedNumber(-5) == "-۵")
    }

    // MARK: Titles & progress

    @Test func testTitles() {
        #expect(en.testTitle(7) == "Test 7")
        #expect(fa.testTitle(14) == "تست ۱۴")
    }

    @Test func progressText() {
        #expect(en.progress(3, 20) == "3 of 20")
        #expect(fa.progress(3, 20) == "۳ از ۲۰")
    }

    // MARK: Feedback thresholds

    @Test(arguments: [
        (20, 20, "Excellent work!"),
        (18, 20, "Excellent work!"),          // exactly 90%
        (17, 20, "Nice job — almost perfect."),
        (14, 20, "Nice job — almost perfect."), // exactly 70%
        (13, 20, "Keep practicing — you're close."),
        (10, 20, "Keep practicing — you're close."), // exactly 50%
        (9, 20, "Give it another go!"),
        (0, 20, "Give it another go!"),
    ])
    func englishFeedback(score: Int, total: Int, expected: String) {
        #expect(en.feedback(score: score, total: total) == expected)
    }

    @Test func persianFeedbackUsesPersianText() {
        #expect(fa.feedback(score: 20, total: 20) == "عالی بود!")
        #expect(fa.feedback(score: 0, total: 20) == "یک بار دیگر امتحان کن.")
    }

    @Test func feedbackIsEmptyWhenThereAreNoQuestions() {
        #expect(en.feedback(score: 0, total: 0) == "")
        #expect(fa.feedback(score: 0, total: 0) == "")
    }

    // MARK: Every string is translated

    @Test func allStaticStringsDifferBetweenLanguagesAndAreNotEmpty() {
        let pairs: [(String, String)] = [
            (en.welcomeTitle, fa.welcomeTitle),
            (en.selectLanguage, fa.selectLanguage),
            (en.selectTest, fa.selectTest),
            (en.mockTest, fa.mockTest),
            (en.mistakes, fa.mistakes),
            (en.next, fa.next),
            (en.finish, fa.finish),
            (en.results, fa.results),
            (en.tryAgain, fa.tryAgain),
            (en.done, fa.done),
            (en.noMistakes, fa.noMistakes),
            (en.emptyTest, fa.emptyTest),
        ]
        for (english, persian) in pairs {
            #expect(!english.isEmpty)
            #expect(!persian.isEmpty)
            #expect(english != persian)
        }
    }
}
