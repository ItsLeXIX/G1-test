//
//  TestMenuView.swift
//  G1 test
//
//  A single, language-agnostic menu that replaces the old duplicated
//  EnglishTestMenuView / PersianTestMenuView. The list of tests is driven
//  by the data in QuestionBank, so it always matches the questions that
//  actually exist — no more dead placeholder buttons.
//

import SwiftUI

struct TestMenuView: View {
    let language: AppLanguage

    @Environment(MistakesStore.self) private var mistakes

    private let columns = [GridItem(.flexible()), GridItem(.flexible())]

    var body: some View {
        let strings = AppStrings(language: language)

        ScrollView {
            LazyVGrid(columns: columns, spacing: 16) {
                // One tile per available test.
                ForEach(QuestionBank.tests(for: language), id: \.self) { test in
                    menuLink(
                        title: strings.testTitle(test),
                        questions: QuestionBank.questions(language: language, test: test),
                        color: .teal
                    )
                }

                // Mock exam: random questions across all tests.
                menuLink(
                    title: strings.mockTest,
                    questions: QuestionBank.mockTest(language: language),
                    color: .indigo
                )

                // Mistakes review.
                let missed = QuestionBank.questions(ids: mistakes.missedIDs, language: language)
                menuLink(
                    title: badged(strings.mistakes, count: missed.count, strings: strings),
                    questions: missed,
                    color: .orange
                )
            }
            .padding()
        }
        .navigationTitle(strings.selectTest)
        .navigationBarTitleDisplayMode(.inline)
        .environment(\.layoutDirection, language.isRightToLeft ? .rightToLeft : .leftToRight)
    }

    // MARK: - Helpers

    @ViewBuilder
    private func menuLink(title: String, questions: [Question], color: Color) -> some View {
        NavigationLink {
            QuizView(viewModel: QuizViewModel(
                title: title,
                language: language,
                questions: questions,
                mistakes: mistakes
            ))
        } label: {
            MenuTile(title: title, color: color)
        }
    }

    private func badged(_ title: String, count: Int, strings: AppStrings) -> String {
        count > 0 ? "\(title) (\(strings.localizedNumber(count)))" : title
    }
}

/// A single grid button used in the test menu.
private struct MenuTile: View {
    let title: String
    var color: Color = .teal

    var body: some View {
        Text(title)
            .fontWeight(.semibold)
            .frame(maxWidth: .infinity, minHeight: 28)
            .padding()
            .background(color, in: .rect(cornerRadius: 12))
            .foregroundStyle(.white)
    }
}

#Preview("English") {
    NavigationStack { TestMenuView(language: .english) }
        .environment(MistakesStore())
}

#Preview("Persian") {
    NavigationStack { TestMenuView(language: .persian) }
        .environment(MistakesStore())
}
