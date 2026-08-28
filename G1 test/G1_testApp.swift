//
//  G1_testApp.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI

@main
struct G1_testApp: App {
    // Single shared store for the user's missed questions, injected into
    // the environment so any screen can read or update it.
    @State private var mistakes = MistakesStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(mistakes)
        }
    }
}
