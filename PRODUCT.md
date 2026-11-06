# Product

<!-- impeccable:product-schema 1 -->

## Platform

ios

## Users
Persian-speaking newcomers in Ontario who are preparing for the G1 written knowledge test. They choose to practise in Persian (فارسی) to understand the material, or in English, the language they may sit the real test in. Typically they study alone on their phone in short sessions before the test.

## Product Purpose
A practice app for the Ontario G1 knowledge test. Learners work through numbered practice tests, take a randomized mock exam and review the questions they got wrong until they answer them correctly. Success means the learner walks into the real test already familiar with the signs and rules questions and passes.

## Positioning
A full, parallel Persian question bank written or reviewed by a person rather than machine-translated, with a matching English bank, so a Farsi speaker can learn in their own language and rehearse in English inside one app.

## Operating Context
- The learner picks a language on launch (English or فارسی) in the app, independent of the device locale. Persian switches the layout to right-to-left and shows Persian digits.
- Study flow: choose a test → answer multiple-choice questions one at a time with immediate feedback → see a score with encouraging feedback → try again or exit.
- Mistakes persist on device. A missed question stays in the Mistakes set until the learner answers it correctly.

## Capabilities and Constraints
- Native SwiftUI app for iPhone and iPad (iOS 18.5+). No account and no backend. State (missed question IDs) lives in UserDefaults.
- Content: `G1 test/questions.json` contains 14 tests × 20 questions per language (en, fa). Signs tests carry an image asset (`Assets.xcassets/QuestionsImages`) and rules tests are text-only. Mock exam = 20 random questions across a language's tests.
- UI strings are centralized in `AppStrings.swift`, keyed on in-app language. Every user-facing string needs both English and Persian.
- Terminology: "Test N", "Mock Test", "Mistakes".
- Business model: paid or freemium is intended. **Open decision:** price, what is free versus paid, and the purchase mechanism are not decided. Do not design pricing, paywalls or upgrade claims as settled facts.

## Brand Commitments
- Name: "G1 Practice Test" / "آزمون تمرینی جی-۱".
- Voice: short, warm, encouraging (e.g. "No mistakes yet. Nice work!" / "هنوز اشتباهی نداری. آفرین!"). Persian copy uses informal second person.
- Persian text is written or reviewed by a person. Never substitute machine translation for Persian copy or question content.

## Evidence on Hand
- Question bank and sign images in the repo (paths above). Welcome illustration at `Assets.xcassets/welcomeImage.imageset`.
- No testimonials, user counts, pass rates, reviews or press exist. Do not fabricate them.
- No confirmed claim that questions are verified against the official MTO Driver's Handbook, and no stated position on official affiliation. Do not claim accuracy guarantees or endorsement.

## Product Principles
1. Persian is a first-class language, not a translation layer: equal content, correct RTL and Persian numerals everywhere.
2. Practice that converges: every wrong answer feeds the Mistakes loop until the learner fixes it.
3. Short sessions on a phone: a test is 20 questions, one at a time, with immediate feedback.
4. Encourage, don't judge. Feedback is supportive at every score.

## Accessibility & Inclusion
Bilingual EN/FA with full right-to-left layout for Persian. No further accessibility standard has been set yet.
