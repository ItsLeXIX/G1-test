//
//  Test1View.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI

struct Test1View: View {
    @Environment(\.managedObjectContext) var context

    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \Question.id, ascending: true)],
        predicate: NSPredicate(format: "id <= %d", 16),
        animation: .default
    ) var questions: FetchedResults<Question>
    
    var body: some View {
        List {
            ForEach(questions, id: \.self) { question in
                VStack(alignment: .leading, spacing: 10) {
                    Text("Q\(question.id): \(question.question ?? "")")
                        .font(.headline)
                    
                    Text("A. \(question.optionA ?? "")")
                    Text("B. \(question.optionB ?? "")")
                    Text("C. \(question.optionC ?? "")")
                    Text("D. \(question.optionD ?? "")")
                }
                .padding(.vertical, 8)
            }
        }
        .navigationTitle("Test 1")
        .onAppear {
            Test1Seeder.seed(context: context)
        }
    }
}
