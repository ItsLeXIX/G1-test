//
//  EnglishTestMenuView.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI

struct EnglishTestMenuView: View {
    let columns = [GridItem(.flexible()), GridItem(.flexible())]
    
    let testButtons = [
        "TEST 1", "TEST 2", "TEST 3", "TEST 4",
        "TEST 5", "TEST 6", "TEST 7", "TEST 8",
        "TEST 9", "TEST 10", "TEST 11", "TEST 12",
        "TEST 13", "TEST 14", "TEST 15", "TEST 16",
        "MOCK TEST", "MISTAKES"
    ]
    
    var body: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 16) {
                ForEach(testButtons, id: \.self) { title in
                    if title == "TEST 1" {
                        NavigationLink(destination: Test1View()) {
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
                    } else {
                        Button(action: {
                            // Placeholder for other tests
                        }) {
                            HStack {
                                Image(systemName: "plus")
                                Text(title)
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.gray)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                    }
                }            }
            .padding()
        }
        .navigationTitle("Select a Test")
    }
}
