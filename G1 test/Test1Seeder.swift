//
//  Test1Seeder.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import CoreData

struct Test1Seeder {
    static func seed(context: NSManagedObjectContext) {
        let fetchRequest: NSFetchRequest<Question> = Question.fetchRequest()
        
        // Avoid seeding again if already seeded
        fetchRequest.predicate = NSPredicate(format: "id == %d", 1)
        let count = (try? context.count(for: fetchRequest)) ?? 0
        if count > 0 {
            print("Test 1 already seeded.")
            return
        }

        let q1 = Question(context: context)
        q1.id = 1
        q1.question = "What does a red traffic light mean?"
        q1.optionA = "Stop"
        q1.optionB = "Go"
        q1.optionC = "Yield"
        q1.optionD = "Speed up"
        q1.correctOption = "A"
        q1.category = "Traffic Signals"
        q1.imageName = ""  // If you have an image, add its name here
        q1.userChoice = ""

        let q2 = Question(context: context)
        q2.id = 2
        q2.question = "When should you yield at an intersection?"
        q2.optionA = "When you see a stop sign"
        q2.optionB = "When entering from a side road"
        q2.optionC = "Only if there are pedestrians"
        q2.optionD = "Never"
        q2.correctOption = "B"
        q2.category = "Right of Way"
        q2.imageName = ""
        q2.userChoice = ""

        // Add more questions here...

        do {
            try context.save()
            print("Test 1 seeded successfully.")
        } catch {
            print("Failed to seed Test 1: \(error)")
        }
    }
}
