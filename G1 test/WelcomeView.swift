//
//  WelcomeView.swift
//  G1 test
//
//  Created by Parsa Jalali on 04.08.25.
//

import SwiftUI

struct WelcomeView: View {
    var body: some View {
        VStack(spacing: 20) {
            Text("Welcome To G1 test Drive")
                .font(.title)
                .fontWeight(.bold)
                .multilineTextAlignment(.center)

            Text("Please select your language")
                .font(.headline)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
            
            Image("welcomeImage")
                .resizable()
                .scaledToFit()
                .frame(height: 250)
            
            VStack(spacing: 16) {
                NavigationLink(destination: EnglishTestMenuView()) {
                    HStack {
                        Image(systemName: "plus")
                        Text("ENGLISH")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.teal)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }

                NavigationLink(destination: PersianTestMenuView()) {
                    HStack {
                        Image(systemName: "plus")
                        Text("فارسی")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.teal)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
            }
            .padding(.horizontal, 40)
            }
        .padding()
    }
}
