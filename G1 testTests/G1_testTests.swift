//
//  G1_testTests.swift  (Models)
//  G1 testTests
//
//  Tests for the core value types in Models.swift.
//

import Foundation
import Testing
@testable import G1_test

@Suite("Models")
struct ModelsTests {

    // MARK: AppLanguage

    @Test func languageRawValuesMatchJSON() {
        #expect(AppLanguage.english.rawValue == "en")
        #expect(AppLanguage.persian.rawValue == "fa")
        #expect(AppLanguage(rawValue: "en") == .english)
        #expect(AppLanguage(rawValue: "fa") == .persian)
        #expect(AppLanguage(rawValue: "de") == nil)
    }

    @Test func languageCasesAndIDs() {
        #expect(AppLanguage.allCases == [.english, .persian])
        #expect(AppLanguage.english.id == "en")
        #expect(AppLanguage.persian.id == "fa")
    }

    @Test func languageDisplayNames() {
        #expect(AppLanguage.english.displayName == "ENGLISH")
        #expect(AppLanguage.persian.displayName == "فارسی")
    }

    @Test func onlyPersianIsRightToLeft() {
        #expect(AppLanguage.persian.isRightToLeft)
        #expect(!AppLanguage.english.isRightToLeft)
    }

    // MARK: QuestionCategory

    @Test func categoryRawValues() {
        #expect(QuestionCategory.signs.rawValue == "signs")
        #expect(QuestionCategory.rules.rawValue == "rules")
        #expect(QuestionCategory(rawValue: "other") == nil)
    }

    // MARK: Question

    @Test(arguments: 0..<4)
    func correctOptionReturnsOptionAtCorrectIndex(index: Int) {
        let q = TestData.question(1, correctIndex: index)
        #expect(q.correctOption == "Correct 1")
        #expect(q.options[index] == "Correct 1")
    }

    @Test(arguments: [-1, 4, 99])
    func correctOptionIsEmptyForMalformedIndex(index: Int) {
        let q = Question(id: "en-1", language: .english, category: .rules, test: 1,
                         text: "Q", options: ["a", "b", "c", "d"],
                         correctIndex: index, imageName: nil)
        #expect(q.correctOption == "")
    }

    @Test func hasImageIsFalseWithoutAName() {
        #expect(!TestData.question(1, imageName: nil).hasImage)
        #expect(!TestData.question(1, imageName: "").hasImage)
    }

    @Test func hasImageIsFalseForMissingAsset() {
        #expect(!TestData.question(1, imageName: "definitely-not-an-asset-9999").hasImage)
    }

    @Test func hasImageIsTrueForBundledAsset() {
        // Image 1 is the first sign picture shipped with the app.
        #expect(TestData.question(1, imageName: "1").hasImage)
    }

    @Test func questionDecodesFromJSON() throws {
        let json = """
        {"id":"fa-7","language":"fa","category":"signs","test":3,
         "text":"متن","options":["a","b","c","d"],"correctIndex":2,"imageName":"47"}
        """
        let q = try JSONDecoder().decode(Question.self, from: Data(json.utf8))
        #expect(q.id == "fa-7")
        #expect(q.language == .persian)
        #expect(q.category == .signs)
        #expect(q.test == 3)
        #expect(q.options.count == 4)
        #expect(q.correctOption == "c")
        #expect(q.imageName == "47")
    }

    @Test func questionDecodesNullImage() throws {
        let json = """
        {"id":"en-1","language":"en","category":"rules","test":2,
         "text":"Q","options":["a","b","c","d"],"correctIndex":0,"imageName":null}
        """
        let q = try JSONDecoder().decode(Question.self, from: Data(json.utf8))
        #expect(q.imageName == nil)
        #expect(!q.hasImage)
    }

    @Test func questionRejectsUnknownLanguage() {
        let json = """
        {"id":"de-1","language":"de","category":"rules","test":1,
         "text":"Q","options":["a","b","c","d"],"correctIndex":0,"imageName":null}
        """
        #expect(throws: DecodingError.self) {
            try JSONDecoder().decode(Question.self, from: Data(json.utf8))
        }
    }

    @Test func questionCodableRoundTrip() throws {
        let original = TestData.question(42, language: .persian, category: .signs,
                                         test: 5, correctIndex: 3, imageName: "85")
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(Question.self, from: data)
        #expect(decoded == original)
    }
}
