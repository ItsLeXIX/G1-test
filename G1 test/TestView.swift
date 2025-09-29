//
//  TestView.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI
import UIKit
import CoreData

private func imageExists(_ name: String) -> Bool {
    return UIImage(named: name) != nil
}

private struct QuizChoice: Identifiable, Hashable {
    let id = UUID()
    let text: String
    let originalKey: String   // "A"/"B"/"C"/"D" as stored in Core Data
    let isCorrect: Bool
}

struct TestView: View {
    // Reusable parameters
    private let testID: Int
    private let questionsPerTest: Int
    private let titleText: String


    @FetchRequest private var questions: FetchedResults<Question>

    @State private var currentIndex = 0
    @State private var selectedOption: String? = nil
    @State private var showAnswer = false
    @State private var showResults = false
    @State private var shuffledQuestions: [Question] = []
    @State private var shuffledChoices: [NSManagedObjectID: [QuizChoice]] = [:]

    init(
        testID: Int = 1,
        questionsPerTest: Int = 20,
        title: String = "G1 Trial Test 1 (English)",
        idStart: Int? = nil
    ) {
        // Ensure database is seeded before building the fetch request
        TestSeeder.seedIfNeeded(context: PersistenceController.shared.container.viewContext)
        self.testID = testID
        self.questionsPerTest = questionsPerTest
        self.titleText = title
        
        let lower: Int
        let upper: Int
        if let idStart = idStart {
            lower = idStart
            upper = idStart + questionsPerTest - 1
        } else {
            lower = (testID - 1) * questionsPerTest + 1
            upper = testID * questionsPerTest
        }


        _questions = FetchRequest(
            entity: Question.entity(),
            sortDescriptors: [NSSortDescriptor(key: "id", ascending: true)],
            predicate: NSPredicate(format: "id >= %d AND id <= %d", lower, upper),
            animation: .default
        )
    }
    
    private func makeShuffledChoices(for q: Question) -> [QuizChoice] {
        let correct = (q.correctOption ?? "").trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        var items: [QuizChoice] = []
        if let a = q.optionA, !a.isEmpty { items.append(QuizChoice(text: a, originalKey: "A", isCorrect: correct == "A")) }
        if let b = q.optionB, !b.isEmpty { items.append(QuizChoice(text: b, originalKey: "B", isCorrect: correct == "B")) }
        if let c = q.optionC, !c.isEmpty { items.append(QuizChoice(text: c, originalKey: "C", isCorrect: correct == "C")) }
        if let d = q.optionD, !d.isEmpty { items.append(QuizChoice(text: d, originalKey: "D", isCorrect: correct == "D")) }
        items.shuffle()
        return items
    }
    
    var body: some View {
        VStack {
            Text(titleText)
                .font(.title3).bold()

            ProgressView(value: Double(currentIndex + 1), total: Double(shuffledQuestions.count))
                .padding()
            Text("\(currentIndex + 1)/\(shuffledQuestions.count)")
                .font(.subheadline)
                .foregroundColor(.secondary)

            if shuffledQuestions.indices.contains(currentIndex) {
                let question = shuffledQuestions[currentIndex]
                let choices = shuffledChoices[question.objectID] ?? []

                Text(question.question ?? "")
                    .font(.headline)
                    .padding()

                if let img = question.imageName, !img.isEmpty, imageExists(img) {
                    Image(img)
                        .resizable()
                        .scaledToFit()
                        .frame(maxHeight: 220)
                        .padding(.bottom, 8)
                }

                VStack(spacing: 10) {
                    ForEach(choices) { choice in
                        ChoiceButton(
                            text: choice.text,
                            isSelected: (selectedOption == choice.originalKey),
                            showAnswer: showAnswer,
                            isCorrect: choice.isCorrect
                        ) {
                            if !showAnswer {
                                selectedOption = choice.originalKey
                                // persist the user's selected original option key (A/B/C/D)
                                let q = question
                                q.userChoice = choice.originalKey
                                try? q.managedObjectContext?.save()
                                showAnswer = true
                            }
                        }
                    }
                }
                .padding()

                Button(action: {
                    if currentIndex + 1 < shuffledQuestions.count {
                        currentIndex += 1
                        selectedOption = nil
                        showAnswer = false
                    } else {
                        showResults = true
                    }
                }) {
                    Text(currentIndex + 1 < shuffledQuestions.count ? "Next" : "Finish")
                        .bold()
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(showAnswer ? Color.blue : Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
                .disabled(!showAnswer)
                .padding()
            }

            Spacer()
        }
        .padding()
        .sheet(isPresented: $showResults) {
            ResultsView(score: computedScore, total: shuffledQuestions.count) {
                // Reset state and clear choices
                currentIndex = 0
                selectedOption = nil
                showAnswer = false
                showResults = false
                if let ctx = shuffledQuestions.first?.managedObjectContext {
                    for q in shuffledQuestions { q.userChoice = "" }
                    try? ctx.save()
                }
                // Re-shuffle for a new session
                shuffledQuestions = questions.shuffled()
                shuffledChoices = Dictionary(uniqueKeysWithValues: shuffledQuestions.map { ($0.objectID, makeShuffledChoices(for: $0)) })
            }
        }
        .onAppear {
            // Build shuffled question order once per view appearance
            if shuffledQuestions.isEmpty {
                shuffledQuestions = questions.shuffled()
                shuffledChoices = Dictionary(uniqueKeysWithValues: shuffledQuestions.map { ($0.objectID, makeShuffledChoices(for: $0)) })
            }
            // DEBUG: log fetched and shuffled IDs
            let ids = questions.map { Int($0.id) }
            let shuffledIDs = shuffledQuestions.map { Int($0.id) }
            print("DEBUG TestView fetched ids=\(ids)")
            print("DEBUG TestView shuffled ids=\(shuffledIDs)")
        }
    }
    
    private var computedScore: Int {
        questions.reduce(0) { acc, q in
            let correct = (q.correctOption ?? "").trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
            let user = (q.userChoice ?? "").trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
            return acc + (correct == user && !correct.isEmpty ? 1 : 0)
        }
    }
}

private struct ChoiceButton: View {
    let text: String
    let isSelected: Bool
    let showAnswer: Bool
    let isCorrect: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: { onSelect() }) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: iconName)
                Text(text)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(background)
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(borderColor, lineWidth: 1)
            )
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(showAnswer && !isSelected) // lock others after reveal
    }

    // MARK: - Visual State
    private var iconName: String {
        if showAnswer {
            return isCorrect ? "checkmark.circle.fill" : (isSelected ? "xmark.circle.fill" : "circle")
        }
        return isSelected ? "largecircle.fill.circle" : "circle"
    }

    private var background: some View {
        let color: Color
        if showAnswer {
            if isCorrect { color = Color.green.opacity(0.30) }
            else if isSelected { color = Color.red.opacity(0.30) }
            else { color = Color.gray.opacity(0.12) }
        } else {
            color = isSelected ? Color.gray.opacity(0.18) : Color.gray.opacity(0.12)
        }
        return RoundedRectangle(cornerRadius: 10).fill(color)
    }

    private var borderColor: Color {
        if showAnswer {
            if isCorrect { return .green }
            if isSelected { return .red }
        }
        return Color.gray.opacity(0.3)
    }
}

private struct ResultsView: View {
    let score: Int
    let total: Int
    var onRetry: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Text("Results").font(.title.bold())
            Text("\(score) / \(total)")
                .font(.system(size: 44, weight: .bold, design: .rounded))
            Text(feedback)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            Button("Try Again") { onRetry() }
                .buttonStyle(.borderedProminent)
        }
        .padding()
    }

    private var feedback: String {
        guard total > 0 else { return "" }
        let pct = Double(score) / Double(total)
        switch pct {
        case 0.9...: return "Excellent work!"
        case 0.7..<0.9: return "Nice job—almost perfect."
        case 0.5..<0.7: return "Keep practicing—you’re close."
        default: return "Give it another go!"
        }
    }
}
