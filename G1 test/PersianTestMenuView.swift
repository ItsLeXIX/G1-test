//
//  PersianTestMenuView.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI

struct PersianTestMenuView: View {
    let columns = [GridItem(.flexible()), GridItem(.flexible())]
    
    let testButtons = [
        "تست ۱", "تست ۲", "تست ۳", "تست ۴",
        "تست ۵", "تست ۶", "تست ۷", "تست ۸",
        "تست ۹", "تست ۱۰", "تست ۱۱", "تست ۱۲",
        "تست ۱۳", "تست ۱۴", "تست ۱۵", "تست ۱۶",
        "امتحان تمرینی", "اشتباه ها"
    ]
    
    var body: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 16) {
                ForEach(testButtons, id: \.self) { title in
                    Button(action: {
                        // Navigation to each test view here
                    }) {
                        HStack {
                            Image(systemName: "plus")
                            Text(title)
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.teal)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                }
            }
            .padding()
        }
        .navigationTitle("Select a Test")
    }
}
