//
//  QuizView.swift
//  G1 test
//
//  Renders a quiz session driven by QuizViewModel. Replaces the old
//  TestView, which mixed Core Data fetching, shuffling, scoring and UI in
//  one place. Here the view only displays state and forwards user taps.
//

import SwiftUI

struct QuizView: View {
    @State private var vm: QuizViewModel
    private let strings: AppStrings

    init(viewModel: QuizViewModel) {
        _vm = State(initialValue: viewModel)
        self.strings = AppStrings(language: viewModel.language)
    }

    var body: some View {
        Group {
            if vm.isEmpty {
                emptyState
            } else {
                quiz
            }
        }
        .navigationTitle(vm.title)
        .navigationBarTitleDisplayMode(.inline)
        .environment(\.layoutDirection, vm.language.isRightToLeft ? .rightToLeft : .leftToRight)
        .sheet(isPresented: $vm.showResults) {
            ResultsView(
                score: vm.correctCount,
                total: vm.total,
                strings: strings,
                onRetry: { vm.restart() }
            )
            .presentationDetents([.medium])
        }
    }

    // MARK: - Quiz content

    private var quiz: some View {
        VStack(spacing: 16) {
            ProgressView(value: vm.progressValue)
            Text(strings.progress(vm.currentIndex + 1, vm.total))
                .font(.subheadline)
                .foregroundStyle(.secondary)

            if let question = vm.currentQuestion {
                ScrollView {
                    VStack(spacing: 16) {
                        Text(question.text)
                            .font(.headline)
                            .multilineTextAlignment(.leading)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        if question.hasImage, let name = question.imageName {
                            Image(name)
                                .resizable()
                                .scaledToFit()
                                .frame(maxHeight: 220)
                        }

                        VStack(spacing: 10) {
                            ForEach(vm.currentChoices) { choice in
                                ChoiceButton(
                                    text: choice.text,
                                    isSelected: vm.selectedChoiceID == choice.id,
                                    isCorrect: choice.isCorrect,
                                    showAnswer: vm.isAnswered
                                ) {
                                    vm.select(choice)
                                }
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }
            }

            Button(action: { vm.advance() }) {
                Text(vm.isLastQuestion ? strings.finish : strings.next)
                    .bold()
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(vm.isAnswered ? Color.blue : Color.gray,
                                in: .rect(cornerRadius: 10))
                    .foregroundStyle(.white)
            }
            .disabled(!vm.isAnswered)
        }
        .padding()
    }

    // MARK: - Empty state

    private var emptyState: some View {
        ContentUnavailableView(
            strings.mistakes,
            systemImage: "checkmark.seal",
            description: Text(strings.noMistakes)
        )
    }
}

// MARK: - Choice button

private struct ChoiceButton: View {
    let text: String
    let isSelected: Bool
    let isCorrect: Bool
    let showAnswer: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: iconName)
                Text(text)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 0)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(background, in: .rect(cornerRadius: 10))
            .overlay(
                RoundedRectangle(cornerRadius: 10).stroke(borderColor, lineWidth: 1)
            )
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(showAnswer && !isSelected) // lock other options after reveal
    }

    private var iconName: String {
        if showAnswer {
            return isCorrect ? "checkmark.circle.fill"
                 : (isSelected ? "xmark.circle.fill" : "circle")
        }
        return isSelected ? "largecircle.fill.circle" : "circle"
    }

    private var background: Color {
        if showAnswer {
            if isCorrect { return .green.opacity(0.30) }
            if isSelected { return .red.opacity(0.30) }
            return .gray.opacity(0.12)
        }
        return isSelected ? .gray.opacity(0.18) : .gray.opacity(0.12)
    }

    private var borderColor: Color {
        if showAnswer {
            if isCorrect { return .green }
            if isSelected { return .red }
        }
        return .gray.opacity(0.3)
    }
}

// MARK: - Results

private struct ResultsView: View {
    let score: Int
    let total: Int
    let strings: AppStrings
    var onRetry: () -> Void

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 16) {
            Text(strings.results).font(.title.bold())

            Text("\(strings.localizedNumber(score)) / \(strings.localizedNumber(total))")
                .font(.system(size: 44, weight: .bold, design: .rounded))

            Text(strings.feedback(score: score, total: total))
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Button(strings.tryAgain) { onRetry() }
                .buttonStyle(.borderedProminent)

            Button(strings.done) { dismiss() }
                .buttonStyle(.bordered)
        }
        .padding()
    }
}

#Preview {
    NavigationStack {
        QuizView(viewModel: QuizViewModel(
            title: "Test 1",
            language: .english,
            questions: QuestionBank.questions(language: .english, test: 1),
            mistakes: MistakesStore()
        ))
    }
}
