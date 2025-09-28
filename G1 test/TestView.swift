//
//  TestView.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI
import CoreData

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
    
    var body: some View {
        VStack {
            Text(titleText)
                .font(.title3).bold()

            ProgressView(value: Double(currentIndex + 1), total: Double(questions.count))
                .padding()
            Text("\(currentIndex + 1)/\(questions.count)")
                .font(.subheadline)
                .foregroundColor(.secondary)

            if questions.indices.contains(currentIndex) {
                let question = questions[currentIndex]

                Text(question.question ?? "")
                    .font(.headline)
                    .padding()

                VStack(spacing: 10) {
                    OptionButton(option: "A", text: question.optionA ?? "", selectedOption: $selectedOption, showAnswer: showAnswer, correctOption: question.correctOption ?? "")
                    OptionButton(option: "B", text: question.optionB ?? "", selectedOption: $selectedOption, showAnswer: showAnswer, correctOption: question.correctOption ?? "")
                    OptionButton(option: "C", text: question.optionC ?? "", selectedOption: $selectedOption, showAnswer: showAnswer, correctOption: question.correctOption ?? "")
                    OptionButton(option: "D", text: question.optionD ?? "", selectedOption: $selectedOption, showAnswer: showAnswer, correctOption: question.correctOption ?? "")
                }
                .padding()
                .onChange(of: selectedOption) { oldValue, newValue in
                    guard let selected = newValue else { return }
                    let q = questions[currentIndex]
                    q.userChoice = selected
                    try? q.managedObjectContext?.save()
                    showAnswer = true
                }

                Button(action: {
                    if currentIndex + 1 < questions.count {
                        currentIndex += 1
                        selectedOption = nil
                        showAnswer = false
                    } else {
                        showResults = true
                    }
                }) {
                    Text(currentIndex + 1 < questions.count ? "Next" : "Finish")
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
            ResultsView(score: computedScore, total: questions.count) {
                // Reset state and clear choices
                currentIndex = 0
                selectedOption = nil
                showAnswer = false
                showResults = false
                if let ctx = questions.first?.managedObjectContext {
                    for q in questions { q.userChoice = "" }
                    try? ctx.save()
                }
            }
        }
        .onAppear {
            // DEBUG: log fetched IDs for this view's current range
            let ids = questions.map { Int($0.id) }
            print("DEBUG TestView fetched ids=\(ids)")
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

private struct OptionButton: View {
    let option: String
    let text: String
    @Binding var selectedOption: String?
    let showAnswer: Bool
    let correctOption: String

    var body: some View {
        Button(action: { if !showAnswer { selectedOption = option } }) {
            HStack(spacing: 12) {
                Image(systemName: iconName)
                Text("\(option). \(text)")
                    .multilineTextAlignment(.leading)
                Spacer()
            }
            .padding(12)
            .background(background)
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(borderColor, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .disabled(showAnswer) // lock after reveal
    }

    // MARK: - Visual State
    private var isSelected: Bool { selectedOption == option }
    private var isCorrect: Bool { option.uppercased() == correctOption.uppercased() }

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
