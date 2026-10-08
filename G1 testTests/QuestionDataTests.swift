//
//  QuestionDataTests.swift
//  G1 testTests
//
//  Guards the content of questions.json. These catch the kind of mistakes
//  that are easy to make when adding a new set by hand: duplicate ids, a
//  missing picture, a wrong answer index, or English and Persian drifting
//  apart.
//

import Foundation
import Testing
@testable import G1_test

@Suite("Question data")
struct QuestionDataTests {
    let all = QuestionBank.all

    private func number(_ id: String) -> Int? {
        id.split(separator: "-").last.flatMap { Int($0) }
    }

    @Test func idsAreUnique() {
        let ids = all.map(\.id)
        #expect(Set(ids).count == ids.count)
    }

    @Test func idsHaveLanguagePrefixAndNumber() {
        for q in all {
            #expect(q.id.hasPrefix(q.language.rawValue + "-"), "\(q.id) has the wrong prefix")
            #expect(number(q.id) != nil, "\(q.id) has no number")
        }
    }

    @Test func everyQuestionHasFourNonEmptyDistinctOptions() {
        for q in all {
            #expect(q.options.count == 4, "\(q.id) has \(q.options.count) options")
            #expect(!q.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, "\(q.id) has no text")
            let trimmed = q.options.map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            #expect(!trimmed.contains(""), "\(q.id) has an empty option")
            #expect(Set(trimmed).count == trimmed.count, "\(q.id) has duplicate options")
        }
    }

    @Test func correctIndexPointsAtAnOption() {
        for q in all {
            #expect(q.options.indices.contains(q.correctIndex), "\(q.id) correctIndex \(q.correctIndex)")
        }
    }

    @Test func noLiteralEscapeCodesInText() {
        // Regression: Test 4 once showed "\u{200C}" on screen instead of a half-space.
        for q in all {
            let text = ([q.text] + q.options).joined()
            #expect(!text.contains("\\u{"), "\(q.id) contains a literal escape code")
        }
    }

    @Test func everyTestHasTwentyQuestions() {
        for language in AppLanguage.allCases {
            for test in QuestionBank.tests(for: language) {
                let count = QuestionBank.questions(language: language, test: test).count
                #expect(count == 20, "\(language.rawValue) test \(test) has \(count) questions")
            }
        }
    }

    @Test func everyImageNameHasABundledAsset() {
        for q in all where q.imageName != nil {
            #expect(q.hasImage, "\(q.id) points at missing image \(q.imageName ?? "")")
        }
    }

    @Test func everySignQuestionHasAPicture() {
        for q in all where q.category == .signs {
            #expect(q.hasImage, "\(q.id) is a sign question without a picture")
        }
    }

    @Test func imageNamesAreNotEmptyStrings() {
        #expect(!all.contains { $0.imageName == "" })
    }

    @Test func englishAndPersianAreExactMirrors() {
        let english = Dictionary(uniqueKeysWithValues:
            all.filter { $0.language == .english }.compactMap { q in number(q.id).map { ($0, q) } })
        let persian = Dictionary(uniqueKeysWithValues:
            all.filter { $0.language == .persian }.compactMap { q in number(q.id).map { ($0, q) } })

        #expect(Set(english.keys) == Set(persian.keys), "English and Persian have different question numbers")

        for (n, fa) in persian {
            guard let en = english[n] else { continue }
            #expect(en.test == fa.test, "#\(n): test differs")
            #expect(en.category == fa.category, "#\(n): category differs")
            #expect(en.correctIndex == fa.correctIndex, "#\(n): correct answer differs")
            #expect(en.imageName == fa.imageName, "#\(n): picture differs")
        }
    }

    @Test func imagesAreNotSharedBetweenDifferentQuestionNumbers() {
        // One picture per question number (English and Persian share it).
        var owner: [String: Int] = [:]
        for q in all {
            guard let image = q.imageName, let n = number(q.id) else { continue }
            if let existing = owner[image] {
                #expect(existing == n, "image \(image) used by #\(existing) and #\(n)")
            } else {
                owner[image] = n
            }
        }
    }
}
