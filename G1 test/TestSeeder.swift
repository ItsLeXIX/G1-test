//
//  TestSeeder.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import Foundation
import CoreData

struct TestSeeder {
    /// Backward compatible entrypoint
    static func seed(context: NSManagedObjectContext) {
        seedIfNeeded(context: context)
    }

    /// Idempotent seeder: inserts questions 1...20 only if they are missing
    static func seedIfNeeded(context: NSManagedObjectContext) {
        func exists(id: Int) -> Bool {
            let r: NSFetchRequest<Question> = Question.fetchRequest()
            r.predicate = NSPredicate(format: "id == %d", id)
            return ((try? context.count(for: r)) ?? 0) > 0
        }

        func add(_ id: Int, _ text: String, _ a: String, _ b: String, _ c: String, _ d: String, _ correct: String, _ category: String) {
            guard !exists(id: id) else { return }
            let q = Question(context: context)
            q.id = Int32(id)
            q.question = text
            q.optionA = a
            q.optionB = b
            q.optionC = c
            q.optionD = d
            q.correctOption = correct
            q.category = category
            q.imageName = ""
            q.userChoice = ""
        }

        // IDs 1...20 (10 Signs, 10 Rules)
        add(1,  "What does a red traffic light mean?", "Stop", "Go", "Yield", "Speed up", "A", "Rules of the Road")
        add(2,  "When should you yield at an intersection?", "When you see a stop sign", "When entering from a side road", "Only if there are pedestrians", "Never", "B", "Rules of the Road")
        add(3,  "What shape is a STOP sign?", "Octagon", "Triangle", "Circle", "Rectangle", "A", "Signs")
        add(4,  "At a four‑way stop, who has the right‑of‑way?", "The largest vehicle", "The vehicle that stops first", "The vehicle on the left", "Whoever flashes headlights", "B", "Rules of the Road")
        add(5,  "A YIELD sign means you must…", "Slow down and give right‑of‑way", "Stop completely every time", "Speed up to merge first", "Ignore if no police are present", "A", "Signs")
        add(6,  "What is the minimum safe following distance in good conditions?", "Two‑second rule", "Half a car length", "One second", "Five car lengths", "A", "Rules of the Road")
        add(7,  "This sign warns of a train crossing ahead. What should you do?", "Speed up to beat the train", "Look, listen, and be prepared to stop", "Turn around immediately", "Park on the tracks briefly", "B", "Signs")
        add(8,  "What must you do when a school bus has flashing red lights?", "Pass carefully on the left", "Slow down and proceed", "Stop from both directions until the lights stop", "Honk and continue", "C", "Rules of the Road")
        add(9,  "‘Divided highway begins’ means…", "A median will separate directions ahead", "Road narrows to one lane", "Two‑way traffic ends", "One‑way street begins", "A", "Signs")
        add(10, "A solid yellow line on your side of the road means…", "No passing", "Passing allowed", "Bus lane", "Bike lane", "A", "Rules of the Road")
        add(11, "This sign means the road may be slippery when wet. What should you do?", "Brake hard", "Slow down and avoid sudden moves", "Turn off headlights", "Speed up to dry the tires", "B", "Signs")
        add(12, "When must you use headlights?", "Only on highways", "Only in rain", "Only outside cities", "From sunset to sunrise or when visibility is poor", "D", "Rules of the Road")
        add(13, "Two‑way traffic ahead sign warns you to…", "Expect traffic only in your lane", "Expect oncoming traffic", "Road closed ahead", "Freeway begins", "B", "Signs")
        add(14, "When an emergency vehicle approaches with lights and siren, you must…", "Maintain speed", "Stop in your lane", "Pull to the right and stop", "Speed up to clear the way", "C", "Rules of the Road")
        add(15, "No‑passing zone (pennant) means…", "Bus lane ahead", "Passing allowed for trucks", "Do not pass in this area", "Keep right of island", "C", "Signs")
        add(16, "What should you do if you start to hydroplane?", "Brake hard and steer sharply", "Accelerate to regain traction", "Ease off the accelerator and steer gently", "Turn off traction control", "C", "Rules of the Road")
        add(17, "Merge sign indicates you should…", "Stop and wait", "Adjust speed and merge when safe", "Make a U‑turn", "Drive on the shoulder", "B", "Signs")
        add(18, "What is the legal blood‑alcohol limit for G1 drivers?", "0.05", "0.00 (zero tolerance)", "0.03", "0.08", "B", "Rules of the Road")
        add(19, "Pedestrian crossing sign means…", "No pedestrians allowed", "Playground ahead", "Pedestrian crossing ahead—be prepared to stop", "School bus stop only", "C", "Signs")
        add(20, "A flashing amber (yellow) traffic light means…", "Stop and wait for green", "Stop, then proceed when safe", "Speed up to clear the intersection", "Proceed with caution", "D", "Rules of the Road")
        
        // Persian Test 1 — IDs 101...120
        add(101, "چراغ قرمز راهنمایی به چه معناست؟", "ایست", "حرکت", "احتیاط", "تند برو", "A", "قوانین رانندگی")
        add(102, "در کدام حالت باید در تقاطع حق تقدم بدهید؟", "وقتی تابلوی توقف می‌بینید", "هنگام ورود از جاده فرعی", "فقط اگر عابر پیاده باشد", "هیچ‌وقت", "B", "قوانین رانندگی")
        add(103, "شکل تابلو ایست چیست؟", "هشت‌ضلعی", "مثلث", "دایره", "مستطیل", "A", "علائم")
        add(104, "در چهارراهی با توقف همزمان، حق تقدم با کیست؟", "بزرگ‌ترین خودرو", "خودرویی که زودتر ایستاده", "خودروی سمت چپ", "کسی که چراغ می‌زند", "B", "قوانین رانندگی")
        add(105, "تابلوی رعایت حق تقدم (Yield) یعنی…", "کاهش سرعت و واگذاری حق تقدم", "همیشه توقف کامل", "برای ادغام سریع‌تر سرعت بگیر", "اگر پلیس نیست، مهم نیست", "A", "علائم")
        add(106, "حداقل فاصله ایمن دنبال‌روی در شرایط خوب چیست؟", "قاعده دو ثانیه", "نیم طول خودرو", "یک ثانیه", "پنج طول خودرو", "A", "قوانین رانندگی")
        add(107, "این علامت هشدار عبور قطار است. چه باید کرد؟", "برای جلو زدن از قطار تند برو", "نگاه کن، گوش بده و آماده توقف باش", "فوراً برگرد", "کمی روی ریل توقف کن", "B", "علائم")
        add(108, "هنگام چشمک‌زدن چراغ‌های قرمز اتوبوس مدرسه چه باید کرد؟", "با احتیاط از چپ سبقت بگیر", "کند شو و عبور کن", "از هر دو جهت توقف تا چراغ‌ها خاموش شود", "بوق بزن و ادامه بده", "C", "قوانین رانندگی")
        add(109, "‘شروع بزرگراه دوطرفه با جداکننده’ یعنی…", "به‌زودی مسیرها با جداکننده از هم جدا می‌شوند", "جاده به یک خط کاهش می‌یابد", "ترافیک دوطرفه تمام می‌شود", "خیابان یک‌طرفه شروع می‌شود", "A", "علائم")
        add(110, "خط زرد پیوسته در کنار شما یعنی…", "سبقت ممنوع", "سبقت آزاد", "خط ویژه اتوبوس", "خط ویژه دوچرخه", "A", "قوانین رانندگی")
        add(111, "این علامت یعنی جاده در هنگام خیس بودن لغزنده است. چه باید کرد؟", "محکم ترمز کن", "سرعت را کم کن و از حرکات ناگهانی بپرهیز", "چراغ‌ها را خاموش کن", "برای خشک شدن لاستیک‌ها سرعت بگیر", "B", "علائم")
        add(112, "چه زمانی باید از چراغ‌های جلو استفاده کنید؟", "فقط در بزرگراه", "فقط در باران", "فقط خارج از شهر", "از غروب تا طلوع یا وقتی دید کم است", "D", "قوانین رانندگی")
        add(113, "علامت ترافیک دوطرفه هشدار می‌دهد که…", "فقط ترافیک در خط شماست", "ترافیک روبه‌رو وجود دارد", "جاده بسته است", "آزادراه شروع می‌شود", "B", "علائم")
        add(114, "هنگام نزدیک شدن خودروی امدادی با چراغ و آژیر چه می‌کنید؟", "با همان سرعت ادامه دهید", "در همان خط توقف کنید", "به راست رفته و توقف کنید", "برای باز کردن راه سرعت بگیرید", "C", "قوانین رانندگی")
        add(115, "تابلوی منطقه ممنوعه سبقت (پرچمی) یعنی…", "خط ویژه اتوبوس", "سبقت برای کامیون‌ها مجاز است", "در این ناحیه سبقت نگیرید", "از سمت راست جزیره حرکت کنید", "C", "علائم")
        add(116, "اگر خودروی شما روی آب سُر بخورد (هیدروپلنینگ)، چه باید کرد؟", "محکم ترمز و تند فرمان دهید", "برای گرفتن چسبندگی گاز بدهید", "از گاز برداشته و به‌ملایمت فرمان دهید", "کنترل کشش را خاموش کنید", "C", "قوانین رانندگی")
        add(117, "علامت ادغام (Merge) یعنی…", "بایست و صبر کن", "سرعت را تنظیم و با احتیاط وارد شوید", "یوترن بزن", "روی شانه راه بران", "B", "علائم")
        add(118, "حد مجاز الکل خون برای راننده گواهینامه G1 چقدر است؟", "۰٫۰۵", "۰٫۰۰ (بدون الکل)", "۰٫۰۳", "۰٫۰۸", "B", "قوانین رانندگی")
        add(119, "علامت عبور عابر پیاده یعنی…", "عبور عابر ممنوع", "زمین بازی پیش‌رو", "عبور عابر پیش‌رو—آماده توقف باشید", "فقط ایستگاه اتوبوس مدرسه", "C", "علائم")
        add(120, "چراغ چشمک‌زن زرد (کهربایی) یعنی…", "بایست و منتظر سبز بمان", "بایست سپس با احتیاط حرکت کن", "برای عبور سریع‌تر سرعت بگیر", "با احتیاط عبور کن", "D", "قوانین رانندگی")

        if context.hasChanges { try? context.save() }
    }
}
