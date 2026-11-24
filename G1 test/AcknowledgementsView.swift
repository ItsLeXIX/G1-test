//
//  AcknowledgementsView.swift
//  G1 test
//
//  Credits for third-party material used in the question images.
//  The two 3D models are CC BY 4.0, which requires this attribution.
//  Keep in sync with tools/question_images/assets/CREDITS.md.
//

import SwiftUI

struct AcknowledgementsView: View {
    private struct Credit: Identifiable {
        let id = UUID()
        let title: String
        let author: String
        let licence: String
        let url: URL
    }

    private let models: [Credit] = [
        Credit(title: "Generic Sedan Car", author: "mmcworks", licence: "CC BY 4.0",
               url: URL(string: "https://sketchfab.com/3d-models/58c33766470d46e7b2aed542650494e5")!),
        Credit(title: "Deciduous Tree with Leaves (medium-Poly)", author: "Sereib", licence: "CC BY 4.0",
               url: URL(string: "https://sketchfab.com/3d-models/6bdc8e61d3c441af872d6fb3f20fd99b")!),
    ]

    private let licenceURL = URL(string: "https://creativecommons.org/licenses/by/4.0/")!

    var body: some View {
        List {
            Section {
                Text("Question images are 3D renders. These models are used under the Creative Commons Attribution 4.0 licence; they were rescaled and placed in the scenes.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }

            Section("3D models") {
                ForEach(models) { credit in
                    Link(destination: credit.url) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("“\(credit.title)”")
                                .font(.body.weight(.semibold))
                            Text("by \(credit.author) · \(credit.licence)")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                Link("Licence: CC BY 4.0", destination: licenceURL)
            }

            Section("Other material") {
                Text("Road sign artwork: Ontario road sign drawings from Wikimedia Commons (public domain).")
                Text("Skies and textures: Poly Haven (CC0).")
            }
            .font(.callout)
        }
        .navigationTitle("Acknowledgements")
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationStack { AcknowledgementsView() }
}
