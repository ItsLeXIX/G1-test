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
                    if title == "تست ۱" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: "تست ۱", idStart: 101)) {
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
                    } else if title == "تست ۲" {
                        NavigationLink(destination: TestView(testID: 2, questionsPerTest: 20, title: "تست ۲", idStart: 121)) {
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
                    } else if title == "تست ۳" {
                        NavigationLink(destination: TestView(testID: 3, questionsPerTest: 20, title: "تست ۳", idStart: 140)) {
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
                    } else if title == "تست ۴" {
                        NavigationLink(destination: TestView(testID: 4, questionsPerTest: 20, title: "تست ۴", idStart: 160)) {
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
                    } else if title == "تست ۵" {
                        NavigationLink(destination: TestView(testID: 5, questionsPerTest: 20, title: "تست ۵", idStart: 181)) {
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
                    } else if title == "تست ۶" {
                        NavigationLink(destination: TestView(testID: 6, questionsPerTest: 20, title: "تست ۶", idStart: 201)) {
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
                    } else if title == "تست ۷" {
                        NavigationLink(destination: TestView(testID: 7, questionsPerTest: 20, title: "تست ۷", idStart: 221)) {
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
                    } else if title == "تست ۸" {
                        NavigationLink(destination: TestView(testID: 8, questionsPerTest: 20, title: "تست ۸", idStart: 241)) {
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
                    } else if title == "تست ۹" {
                        NavigationLink(destination: TestView(testID: 9, questionsPerTest: 20, title: "تست ۹", idStart: 261)) {
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
                    } else if title == "تست ۱۰" {
                        NavigationLink(destination: TestView(testID: 10, questionsPerTest: 20, title: "تست ۱۰", idStart: 281)) {
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
                    } else if title == "تست ۱۱" {
                        NavigationLink(destination: TestView(testID: 11, questionsPerTest: 20, title: "تست ۱۱", idStart: 301)) {
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
                    } else if title == "تست ۱۲" {
                        NavigationLink(destination: TestView(testID: 12, questionsPerTest: 20, title: "تست ۱۲", idStart: 321)) {
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
                    } else if title == "تست ۱۳" {
                        NavigationLink(destination: TestView(testID: 13, questionsPerTest: 20, title: "تست ۱۳", idStart: 341)) {
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
                    } else if title == "تست ۱۴" {
                        NavigationLink(destination: TestView(testID: 14, questionsPerTest: 20, title: "تست ۱۴", idStart: 361)) {
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
                    } else if title == "تست ۱۵" {
                        NavigationLink(destination: TestView(testID: 15, questionsPerTest: 20, title: "تست ۱۵", idStart: 381)) {
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
                    } else if title == "تست ۱۶" {
                        NavigationLink(destination: TestView(testID: 16, questionsPerTest: 20, title: "تست ۱۶", idStart: 401)) {
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
                    } else if title == "تست ۱۷" {
                        NavigationLink(destination: TestView(testID: 17, questionsPerTest: 20, title: "تست ۱۷", idStart: 421)) {
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
                    } else if title == "تست ۱۸" {
                        NavigationLink(destination: TestView(testID: 18, questionsPerTest: 20, title: "تست ۱۸", idStart: 441)) {
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
                    } else if title == "تست ۱۹" {
                        NavigationLink(destination: TestView(testID: 19, questionsPerTest: 20, title: "تست ۱۹", idStart: 461)) {
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
                    } else if title == "تست ۲۰" {
                        NavigationLink(destination: TestView(testID: 20, questionsPerTest: 20, title: "تست ۲۰", idStart: 481)) {
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
                    } else {
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
