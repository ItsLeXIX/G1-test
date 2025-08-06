//
//  G1_testApp.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI

@main
struct G1_testApp: App {
    let persistenceController = PersistenceController.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
        }
    }
}
