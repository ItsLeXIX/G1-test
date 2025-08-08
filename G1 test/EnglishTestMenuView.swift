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
        "Test 17", "Test 18", "Test 19", "Test 20",
        "MOCK TEST", "MISTAKES"
    ]
    
    var body: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 16) {
                ForEach(testButtons, id: \.self) { title in
                    if title == "TEST 1" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "TEST 1", idStart: 1)) {
                            HStack {
                                Text(title)
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.teal)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                    }else if title == "TEST 2" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "TEST 2", idStart: 21)) {
                            HStack {
                                Text(title)
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.teal)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                    }else if title == "TEST 3" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "TEST 3", idStart: 31)) {
                            HStack {
                                Text(title)
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.teal)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                    }else if title == "TEST 4" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "TEST 4", idStart: 41)) {
                            HStack {
                                Text(title)
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.teal)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                    }else if title == "TEST 5" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "TEST 5", idStart: 51)) {
                            HStack {
                                Text(title)
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.teal)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                    }else if title == "TEST 5" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "TEST 5", idStart: 51)) {
                            HStack {
                                Text(title)
                                    .fontWeight(.semibold)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.teal)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                    }else if title == "TEST 6" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "TEST 6", idStart: 61)) {
                            HStack {
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

                    else {
                        Button(action: {
                            // Placeholder for other tests
                        }) {
                            HStack {
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
