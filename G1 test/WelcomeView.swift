//
//  WelcomeView.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI

/// Landing screen: shows the app title and lets the user pick a language.
struct WelcomeView: View {
    var body: some View {
        VStack(spacing: 24) {
            Text("G1 Practice Test")
                .font(.largeTitle.bold())
                .multilineTextAlignment(.center)

            Text("آزمون تمرینی جی-۱")
                .font(.title3)
                .foregroundStyle(.secondary)

            Image("welcomeImage")
                .resizable()
                .scaledToFit()
                .frame(height: 240)
                .accessibilityHidden(true)

            VStack(spacing: 16) {
                ForEach(AppLanguage.allCases) { language in
                    NavigationLink {
                        TestMenuView(language: language)
                    } label: {
                        Text(language.displayName)
                            .fontWeight(.semibold)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.teal, in: .rect(cornerRadius: 12))
                            .foregroundStyle(.white)
                    }
                }
            }
            .padding(.horizontal, 40)
        }
        .padding()
    }
}

#Preview {
    NavigationStack { WelcomeView() }
        .environment(MistakesStore())
}
