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

        // --- Reset Persian ranges: delete any existing 100...139 to avoid stale data ---
        do {
            let fetch: NSFetchRequest<Question> = Question.fetchRequest()
            fetch.predicate = NSPredicate(format: "id >= %d AND id <= %d", 100, 139)
            let old = try context.fetch(fetch)
            for obj in old { context.delete(obj) }
            if context.hasChanges { try context.save() }
        } catch {
            print("Warning: could not delete old Persian questions (100...139): \(error)")
        }

        // Persian Test 1 — IDs 100...119 (Signs)
        add(100, "اين علامت ساختمانى به چه معناست؟",
                    "خیابان سنگفرش آسياب شده يا شياردار است",
                    "عمليات راهدارى در پيش است.", "تابلوى ساخت و ساز جایگزین پرچمدار در حال انجام وظيفه.",
                    "علامت ساخت و ساز براى كاهش سرعت و اطاعت از جهت پرچم.", "B", "علائم")

                add(101, "اين تابلوى راه به چه معناست؟",
                    "شما بايد به چپ بپیچید.", "بايد به راست بپیچید",
                    "شما بايد مستقيم برويد.", "همه چرخش ها مجاز است.", "B", "علائم")

                add(102, "اين تابلوى راه پشت خودرو به چه معناست؟",
                    "خودرویی با سرعت كم", "تابلوى ايست در پيش رو",
                    "وسيله نقليه دارای حمل مواد خطرناك", "حق تقدم را بدهيد", "A", "علائم")

                add(103, "اين تابلوى راه به چه معناست?",
                    "هتل", "مسابقه اسب دوانى", "تپه ها", "بيمارستان", "D", "علائم")

                add(104, "اين تابلوى راه به چه معناست؟",
                    "هیچ چیز مجاز نيست", "دور برگردان مجاز است",
                    "گردش به چپ ممنوع", "دور زدن ممنوع است", "D", "علائم")

                add(105, "اين تابلوى راه به چه معناست؟",
                    "هواپيما وجود دارد.", "فرود هواپیما", "مسير به يك فرودگاه.", "نمايش هوايي در پيش است.", "C", "علائم")

                add(106, "اين تابلوى راه به چه معناست؟",
                    "پارک کردن به سمت راست", "اين جاده كمى به سمت راست در جلو مى چرخد.",
                    "اين جاده جلوتر به طور تند به سمت راست مى چرخد", "ترافيك بايد از راست خارج شود.", "C", "علائم")

                add(107, "اين تابلوى راه به چه معناست؟",
                    "گردش به چب ممنوع.", "مستقيم رفتن مجاز نيست.",
                    "مستقيم رفتن مجاز است.", "گردش به راست مجاز نيست.", "B", "علائم")

                add(108, "اين تابلوى راه به چه معناست؟",
                    "اب روى جاده است", "سطح جاده ناهموار يا پر از دست انداز در پيش رو",
                    "جاده باريك در پيش رو", "پل در پيش رو بالا می‌رود تا اجازه عبور قايقها رابدهد", "D", "علائم")

                add(109, "اين تابلوى راه به چه معناست؟",
                    "شما بايد حق تقدم را بدهيد.", "شما حق تقدم داريد.",
                    "در جلو منطقه مدرسه است.", "در جلو يك تقاطع راه آهن قرار دارد.", "A", "علائم")

                add(110, "اين علامت نشان مى دهد",
                    "يك وضعيت موقت", "يك ممنوعيت", "اخطار", "اطلاعات و جهت", "B", "علائم")

                add(111, "اين تابلوى راه به چه معناست؟",
                    "فقط پاركينك ماشين برفى (اسنوموبيل)", "ماشين هاى برفى (اسنوموبيل) مى توانند از اين جاده استفاده كنند",
                    "عبور ماشين برفى (اسنوموبيل) از اين جاده ممنوع است", "تعميركاه ماشين برفى (اسنوموبيل) در پيش است.", "B", "علائم")

                add(112, "اين علامت به چه معناست؟",
                    "فاصله مشخصى را حفظ كنيد", "در جلو عمليات ساختمانى در حال انجام است",
                    "راه جلوتر بسته است! در ترافيك ادغام شويد", "علائم مسير انحرافى را دنبال كنيد تا به مسير اصلى بازگردید", "D", "علائم")

                add(113, "اين تابلوى راه به چه معناست؟",
                    "چراغ راهنمای ترافيكى در پيش رو.", "تقاطع راه آهن جلوتر.",
                    "تابلو ايست در پيش رو.", "دست انداز در پيش رو.", "A", "علائم")

                add(114, "اين تابلوى راه به چه معناست؟",
                    "روشن گذاشتن موتور خودرو در حالت ساکن برای بیش از ۳ دقیقه ممنوع است.", "توقف بيش از 3 دقيقه غیر مجاز است",
                    "بيش از 3 دقيقه سیگار نكشيد", "پارک کردن خودرو در این محدوده به مدت ۳ دقیقه مجاز است.", "A", "علائم")

                add(115, "اين تابلوى راه به چه معناست؟",
                    "مراقب عابران پياده باشيد", "سرعت خود را كم نكنيد.",
                    "تقاطع را مسدود نكنيد.", "در تقاطع سرعت خود را افزايش دهيد.", "C", "علائم")

                add(116, "اين تابلوى راه به چه معناست؟",
                    "سبقت گرفتن ممنوع", "پارك ممنوع", "ورود سواری ممنوع", "توقف نکنید", "A", "علائم")

                add(117, "اين تابلوى راه به چه معناست؟",
                    "گردش به راست مجاز نيست.", "گردش به چپ مجاز نيست.",
                    "يك جاده فرعى پنهان در جلو وجود دارد.", "دور برگردان مجاز نيست.", "C", "علائم")

                add(118, "اين تابلوى راه به چه معناست؟",
                    "پارک ممنوع", "توقف ممنوع", "ورود دوچرخه به اين جاده ممنوع است.", "دوچرخه ها در اين جاده مجاز هستند.", "C", "علائم")

                add(119, "اين تابلوى راه به چه معناست؟",
                    "اجازه پارك در هر زمانى وجود ندارد.", "شما نمى توانيد در زمان هاى اعلام شده بين تابلوها پارك كنيد.",
                    "شما مى توانيد در منطقه مشخص شده در زمان هاى اعلام شده پارك كنيد.", "فقط پارک کردن در آخر هفته ممنوع نيست.", "C", "علائم")

                // --- Persian Test 2: Rules (IDs 120...139) ---
                add(120, "اگر راننده‌اى به دليل بى‌احتياطى رانندگى محكوم شود، شش امتياز منفى دريافت مى‌كند و مى‌تواند با چه چيزى مواجه شود؟",
                    "همه موارد فوق", "جريمه تا 2000 دلار", "حبس تا شش ماه", "تعليق مجوز تا دوسال", "A", "قوانین رانندگی")

                add(121, "هنگام رانندگى در يك خيابان دوطرفه صداى آژير وسيله نقليه اضطرارى را مى‌شنويد، قانون شما را ملزم به چه كارى مى‌كند؟",
                    "سرعت بگيريد و از مسير خارج شويد", "به راننده علامت بدهيد كه عبور كند",
                    "تا جايى كه امكان دارد به راست بكشيد و متوقف شويد", "با همان سرعت ادامه دهيد", "C", "قوانین رانندگی")

                add(122, "هنگام رانندگى اگر تماسى دريافت كنيد و كسى نيست كه پاسخ دهد، چه كارى بايد بكنيد؟",
                    "قبل از استفاده از تلفن كنار بكشيد و پارك كنيد", "به تلفن پاسخ دهيد و سريع قطع كنيد",
                    "فوراً تلفن را پاسخ دهيد", "پيامك بدهيد كه در حال رانندگى هستيد", "A", "قوانین رانندگی")

                add(123, "چراغ سبز چشمك‌زن در تقاطع يعنى…",
                    "مى‌توانيد به راست بپيچيد", "مى‌توانيد مستقيم برويد", "همه موارد فوق", "مى‌توانيد به چپ بپيچيد", "C", "قوانین رانندگی")

                add(124, "در چه شرايطى مى‌توان گواهينامه رانندگى را باطل كرد؟",
                    "هريك از شرايط فوق", "دستكارى يا جعل گواهينامه", "عدم موفقيت در بازآزمون", "عدم حضور در آزمون يا معاينه پزشكى الزامى", "A", "قوانین رانندگی")

                add(125, "محكوميت به فرار از پليس: تعليق گواهينامه تا چه مدت؟",
                    "5 سال", "5 هفته", "5 ماه", "3 روز", "A", "قوانین رانندگی")

                add(126, "راننده G2، 19 ساله با بيش از 6 ماه تجربه: بين نيمه‌شب تا 5 صبح چند مسافر ناشناس 19 ساله يا كمتر مى‌تواند حمل كند؟",
                    "2", "4", "1", "3", "D", "قوانین رانندگی")

                add(127, "در انتاريو شب‌ها كى بايد نوربالا را كم كنيد؟",
                    "وقتى 150 مترى وسيله نقليه ديگر هستيد", "وقتى 400 مترى وسيله نقليه ديگر هستيد",
                    "وقتى 60 مترى روبه‌رو يا 150 مترى خودرویى كه دنبال مى‌كنيد هستيد", "وقتى 150 مترى روبه‌رو يا 60 مترى خودرویى كه دنبال مى‌كنيد هستيد", "D", "قوانین رانندگی")

                add(128, "وقتى در ميدان هستيد…",
                    "در جهت عقربه‌هاى ساعت برانيد", "مى‌توانيد خط را تغيير دهيد", "مى‌توانيد متوقف شويد", "در خلاف جهت عقربه‌هاى ساعت برانيد", "D", "قوانین رانندگی")

                add(129, "به تقاطعى مى‌رسيد كه چراغ‌ها كار نمى‌كنند. چه بايد كرد؟",
                    "حق تقدم را رها نكنيد", "سرعت را كم كنيد و با احتياط ادامه دهيد",
                    "مثل چهارراه داراى تابلو توقف رفتار كنيد", "سرعت گرفته و با احتياط ادامه دهيد", "C", "قوانین رانندگی")

                add(130, "چراغ قرمز است و افسر پليس به شما اشاره مى‌كند عبور كنيد. چه مى‌كنيد؟",
                    "بايستيد و مطمئن شويد", "صبر كنيد تا سبز شود", "عبور كنيد", "به افسر بگوييد چراغ قرمز است", "C", "قوانین رانندگی")

                add(131, "لاستيك شما ناگهان مى‌تركد. چه مى‌كنيد؟",
                    "خودرو را خارج از جاده متوقف كنيد", "تمركز را بر هدايت بگذاريد", "تمام موارد بالا", "پا را از روى گاز برداريد", "C", "قوانین رانندگی")

                add(132, "نزديك تقاطع چراغ از سبز به زرد تغيير مى‌كند. چه كنيد؟",
                    "سرعت را زياد كنيد و عبور كنيد", "اگر ايمن است توقف كنيد؛ وگرنه با احتياط عبور كنيد",
                    "به عابرين هشدار دهيد", "به رانندگان هشدار دهيد", "B", "قوانین رانندگی")

                add(133, "راننده داراى گواهينامه كامل با 15 امتياز منفى: تعليق به مدت…",
                    "1 هفته", "2 هفته", "30 روز", "3 ماه", "C", "قوانین رانندگی")

                add(134, "در تصادف داراى مصدوم، بايد حادثه را به چه كسى گزارش كنيد؟",
                    "پليس بلافاصله", "وزارت حمل و نقل بلافاصله", "پليس ظرف 48 ساعت", "وزارت حمل و نقل ظرف 48 ساعت", "A", "قوانین رانندگی")

                add(135, "حداقل فاصله هنگام سبقت از دوچرخه‌سوار؟",
                    "2 متر", "1.5 متر", "1 متر", "0.5 متر", "C", "قوانین رانندگی")

                add(136, "تغيير آدرس يا نام: تا چه زمانى بايد به وزارت اطلاع دهيد؟",
                    "10 روز", "6 روز", "2 هفته", "1 ماه", "B", "قوانین رانندگی")

                add(137, "راننده G1/G2 با الكل يا مواد مخدر: با كدام مجازات‌ها مواجه مى‌شود؟",
                    "همه موارد فوق", "تعليق 30 روزه پس از محكوميت", "تعليق فورى 3 روزه", "جريمه 60 تا 500 دلار پس از محكوميت", "A", "قوانین رانندگی")

                add(138, "اتوبوس مدرسه با چراغ قرمز چشمك‌زن و بازوى توقف باز ايستاده است…",
                    "بهتر است حداقل 20 متر فاصله بگيريد", "اگر در طرف مقابل هستيد مى‌توانيد ادامه دهيد",
                    "بايد حداقل 20 متر فاصله بگيريد", "سرعت را تا 20 كيلومتر كاهش دهيد", "C", "قوانین رانندگی")

                add(139, "به علامت ادغام ترافيك نزديك مى‌شويد. چه مى‌كنيد؟",
                    "بوق بزنيد", "سرعت و موقعيت را تنظيم كنيد", "اول اجازه دهيد ماشين‌هاى پشت بروند", "توقف كامل كرده سپس حركت كنيد", "B", "قوانین رانندگی")

                if context.hasChanges { try? context.save() }
            }
        }
