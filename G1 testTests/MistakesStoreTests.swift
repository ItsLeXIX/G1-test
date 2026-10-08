//
//  MistakesStoreTests.swift
//  G1 testTests
//

import Foundation
import Testing
@testable import G1_test

@Suite("MistakesStore")
struct MistakesStoreTests {

    @Test func startsEmpty() {
        let (store, _) = TestData.isolatedMistakes()
        #expect(store.missedIDs.isEmpty)
        #expect(store.count(for: .english) == 0)
        #expect(store.count(for: .persian) == 0)
    }

    @Test func recordAddsID() {
        let (store, _) = TestData.isolatedMistakes()
        store.record("en-101")
        #expect(store.missedIDs == ["en-101"])
    }

    @Test func recordingTwiceKeepsOneEntry() {
        let (store, _) = TestData.isolatedMistakes()
        store.record("en-101")
        store.record("en-101")
        #expect(store.missedIDs.count == 1)
    }

    @Test func clearRemovesID() {
        let (store, _) = TestData.isolatedMistakes()
        store.record("en-101")
        store.record("en-102")
        store.clear("en-101")
        #expect(store.missedIDs == ["en-102"])
    }

    @Test func clearingUnknownIDIsHarmless() {
        let (store, _) = TestData.isolatedMistakes()
        store.record("en-101")
        store.clear("fa-999")
        #expect(store.missedIDs == ["en-101"])
    }

    @Test func clearAllRemovesEverything() {
        let (store, defaults) = TestData.isolatedMistakes()
        store.record("en-101")
        store.record("fa-101")
        store.clearAll()
        #expect(store.missedIDs.isEmpty)
        #expect(MistakesStore(defaults: defaults).missedIDs.isEmpty)
    }

    @Test func countIsPerLanguage() {
        let (store, _) = TestData.isolatedMistakes()
        store.record("en-101")
        store.record("en-102")
        store.record("fa-101")
        #expect(store.count(for: .english) == 2)
        #expect(store.count(for: .persian) == 1)
    }

    @Test func countMatchesPrefixExactly() {
        // "fa-" must not match ids that merely contain "fa" elsewhere.
        let (store, _) = TestData.isolatedMistakes()
        store.record("en-fa-1")
        #expect(store.count(for: .persian) == 0)
        #expect(store.count(for: .english) == 1)
    }

    @Test func mistakesPersistAcrossInstances() {
        let (store, defaults) = TestData.isolatedMistakes()
        store.record("en-101")
        store.record("fa-205")

        let reloaded = MistakesStore(defaults: defaults)
        #expect(reloaded.missedIDs == ["en-101", "fa-205"])
    }

    @Test func clearPersistsAcrossInstances() {
        let (store, defaults) = TestData.isolatedMistakes()
        store.record("en-101")
        store.record("en-102")
        store.clear("en-101")

        let reloaded = MistakesStore(defaults: defaults)
        #expect(reloaded.missedIDs == ["en-102"])
    }

    @Test func loadsPreviouslySavedIDs() {
        let (_, defaults) = TestData.isolatedMistakes()
        defaults.set(["fa-1", "fa-2"], forKey: "missedQuestionIDs")
        let store = MistakesStore(defaults: defaults)
        #expect(store.missedIDs == ["fa-1", "fa-2"])
    }
}
