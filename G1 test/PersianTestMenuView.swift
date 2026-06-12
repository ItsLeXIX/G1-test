import SwiftUI

struct PersianTestMenuView: View {
    let columns = [GridItem(.flexible()), GridItem(.flexible())]

    let testButtons = [
        "تست ۱", "تست ۲", "تست ۳", "تست ۴",
        "تست ۵", "تست ۶", "تست ۷", "تست ۸",
        "تست ۹", "تست ۱۰", "تست ۱۱", "تست ۱۲",
        "تست ۱۳", "تست ۱۴",
        "امتحان تمرینی", "اشتباه‌ها"
    ]

    var body: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 16) {
                ForEach(testButtons, id: \.self) { title in
                    if title == "تست ۱" {
                        NavigationLink(destination: TestView(testID: 1, questionsPerTest: 20, title: title, idStart: 101)) {
                            testButton(title)
                        }
                    } else if title == "تست ۲" {
                        NavigationLink(destination: TestView(testID: 2, questionsPerTest: 20, title: title, idStart: 121)) {
                            testButton(title)
                        }
                    } else if title == "تست ۳" {
                        NavigationLink(destination: TestView(testID: 3, questionsPerTest: 20, title: title, idStart: 141)) {
                            testButton(title)
                        }
                    } else if title == "تست ۴" {
                        NavigationLink(destination: TestView(testID: 4, questionsPerTest: 20, title: title, idStart: 161)) {
                            testButton(title)
                        }
                    } else if title == "تست ۵" {
                        NavigationLink(destination: TestView(testID: 5, questionsPerTest: 20, title: title, idStart: 181)) {
                            testButton(title)
                        }
                    } else if title == "تست ۶" {
                        NavigationLink(destination: TestView(testID: 6, questionsPerTest: 20, title: title, idStart: 201)) {
                            testButton(title)
                        }
                    } else if title == "تست ۷" {
                        NavigationLink(destination: TestView(testID: 7, questionsPerTest: 20, title: title, idStart: 221)) {
                            testButton(title)
                        }
                    } else if title == "تست ۸" {
                        NavigationLink(destination: TestView(testID: 8, questionsPerTest: 20, title: title, idStart: 241)) {
                            testButton(title)
                        }
                    } else if title == "تست ۹" {
                        NavigationLink(destination: TestView(testID: 9, questionsPerTest: 20, title: title, idStart: 261)) {
                            testButton(title)
                        }
                    } else if title == "تست ۱۰" {
                        NavigationLink(destination: TestView(testID: 10, questionsPerTest: 20, title: title, idStart: 281)) {
                            testButton(title)
                        }
                    } else if title == "تست ۱۱" {
                        NavigationLink(destination: TestView(testID: 11, questionsPerTest: 20, title: title, idStart: 301)) {
                            testButton(title)
                        }
                    } else if title == "تست ۱۲" {
                        NavigationLink(destination: TestView(testID: 12, questionsPerTest: 20, title: title, idStart: 321)) {
                            testButton(title)
                        }
                    } else if title == "تست ۱۳" {
                        NavigationLink(destination: TestView(testID: 13, questionsPerTest: 20, title: title, idStart: 341)) {
                            testButton(title)
                        }
                    } else if title == "تست ۱۴" {
                        NavigationLink(destination: TestView(testID: 14, questionsPerTest: 20, title: title, idStart: 361)) {
                            testButton(title)
                        }
                    } else {
                        testButton(title)
                    }
                }
            }
            .padding()
        }
        .navigationTitle("آزمون‌های فارسی")
    }

    private func testButton(_ title: String) -> some View {
        Text(title)
            .fontWeight(.semibold)
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.teal)
            .foregroundColor(.white)
            .cornerRadius(10)
    }
}
