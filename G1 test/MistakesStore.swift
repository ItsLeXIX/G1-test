//
//  MistakesStore.swift
//  G1 test
//
//  Remembers which questions the user has answered incorrectly so they can
//  be reviewed in the "Mistakes" practice set. Backed by UserDefaults, which
//  is the right tool for this small amount of data (a set of question ids).
//

import Foundation
import Observation

@Observable
final class MistakesStore {
    private let key = "missedQuestionIDs"
    private let defaults: UserDefaults

    /// Ids of questions the user has gotten wrong and not yet corrected.
    private(set) var missedIDs: Set<String>

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        let saved = defaults.stringArray(forKey: key) ?? []
        self.missedIDs = Set(saved)
    }

    /// Number of missed questions for a given language (for menu badges).
    func count(for language: AppLanguage) -> Int {
        missedIDs.filter { $0.hasPrefix(language.rawValue + "-") }.count
    }

    func record(_ id: String) {
        guard !missedIDs.contains(id) else { return }
        missedIDs.insert(id)
        persist()
    }

    /// Called when a previously-missed question is answered correctly.
    func clear(_ id: String) {
        guard missedIDs.contains(id) else { return }
        missedIDs.remove(id)
        persist()
    }

    func clearAll() {
        missedIDs.removeAll()
        persist()
    }

    private func persist() {
        defaults.set(Array(missedIDs), forKey: key)
    }
}
