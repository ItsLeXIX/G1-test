# Image regeneration prompt — G1 app

Copied from the G1 claude.ai Project doc.

TASK: Redraw every question image in my G1 practice app

Context
This is an iOS app for practising the Ontario G1 knowledge test. Questions are in
"G1 test/questions.json". Any question with an "imageName" field shows a picture from
"G1 test/Assets.xcassets/QuestionsImages/<imageName>.imageset/". English and Persian
questions use the same images, so each image only needs to be redone once.

Goal
Make a new image for every question that has a picture. Use the current images as
inspiration, but replace all of them.

Before you draw anything
For each image, read the question text and the correct answer in questions.json and look
at the current picture. Work out three things:
1. Which sign, signal or marking the question is about
2. What the scene is
3. What the weather and lighting are

1. Signs: precision comes first
- Use only real, official Canadian road signs, using the Ontario version wherever one
  exists, as they appear in the MTO Driver's Handbook.
- Do not change the sign in any way. Keep its exact shape, colours, border, symbol,
  arrow direction, text, font, numbers and proportions.
- Do not invent, simplify or "artistically interpret" a sign. Don't use US or European
  look-alikes.
- If the current picture shows the wrong sign, or one that doesn't match the correct
  answer, use the correct official Canadian sign and note the change.
- The sign must be sharp, easy to read and face the viewer clearly. It is the subject
  of the image.
- If you can't reproduce a sign exactly, put the official sign artwork (vector or
  reference image) into the scene instead of generating it. Don't accept a distorted
  version.

2. Background: match the setting of the current picture
- Road: draw a road.
- Highway: draw a highway.
- Parking lot: draw a parking lot.
- City street: draw a city street with buildings.
- Overhead sign: draw it mounted overhead.
- Vehicle, hand signal or intersection scenes: keep the same situation and viewpoint.
- Rain, snow, night or wet pavement: draw it that way. Weather matters.
- The background has to fit the sign's meaning. For example, a "pavement ends" sign
  needs the road to actually turn to gravel ahead, and a railway sign needs tracks.
- Make it look like Ontario: Canadian road markings, curbs and vehicles.

3. Style
- Fairly realistic, like a clean photo or a high-quality 3D render, not cartoonish.
- Keep the look the same across all images: camera height, lighting quality and colour
  grading.
- The background can be slightly soft so the sign stands out.
- No logos, car brands, watermarks or extra text, and no other signs that could confuse
  the question.

Output
- Use the same wide aspect ratio as the current images, about 2.4:1.
- Export as high-resolution PNG.
- Save each image into its existing imageset folder under the same asset name, so
  questions.json doesn't need to change.
- At the end, give me a list of every image you made, plus any where you changed the
  sign or the scene, and why.

## Notes
- Image generators often get sign symbols and text slightly wrong, so inserting the
  official sign artwork is the most reliable way to get exact signs.
