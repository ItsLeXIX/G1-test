# G1 image re-render — handoff

Rules for the images: `render_pipeline/image-regeneration-prompt.md`.

## Done
- `render_pipeline/manifest.json`: 101 entries (one per imageName used in `G1 test/questions.json`). Each entry has the signs, scene type, weather, camera preset, and a `change` field when the sign or scene differs from the current image.
- `render_pipeline/build_manifest.py` regenerates it: `python render_pipeline/build_manifest.py "G1 test/questions.json" render_pipeline/manifest.json`
- Image sets 22 and 24 are unused and skipped.
- Contact sheets of the current images: `_sheets/sheet00-08.jpg`

## Open questions for Parsa
- #96: the answer is "road splits in two", but the current image looks like a lane-addition sign. Which sign should it be?
- #102: the advisory speed tab currently says "XX". Proposed: 40 km/h.
- To check against official artwork: #16 (colour), #88 (colour), #55 (vehicle list), #153 (symbol), #15 (municipal no-idling), #141 (diamond shape).

## Next steps (original request)
1. Sign artwork: get the official Canadian/Ontario artwork into `render_pipeline/sign_assets/` and list any you can't find. Never redraw a sign; use the artwork as an image texture on a plate of the correct shape.
2. Scene templates as Python functions: roadside, highway, city street, parking lot, overhead mount, vehicle rear / hand signal, aerial intersection. Weather options: clear, rain/wet, snow, night (manifest also uses dusk).
3. `render.py`: takes manifest entries, builds the scene, renders, saves. Supports `--only 57`. Run headless: `blender -b -P render_pipeline/render.py -- --only 57`
4. Cycles if fast enough on this GPU, otherwise EEVEE. Report which one was picked and the time per image. Output 2400x1000 PNG, with the same camera height, lens and colour management for every image. The sign must be sharp; light depth of field on the background is fine.
5. Before writing any images, back up the old ones outside `Assets.xcassets`. Save each new PNG into `G1 test/Assets.xcassets/QuestionsImages/<n>.imageset/` and update that folder's `Contents.json`. Don't touch `questions.json`.
6. Render 3 samples first (one roadside, one overhead, one with weather) and wait for approval before rendering the rest.
7. Final check of every image: the sign matches the official artwork and the correct answer, and the file is in the right imageset.

## Status 2026-11-05 — Test 1 (images 1–20) rendered, not installed
- Cached-scene workflow (headless, portable Blender 5.2.3 at C:\Users\parsa\Apps\blender-5.2.3-windows-x64):
  1. `blender -b --factory-startup -P render_pipeline/build_scenes.py` → `render_pipeline/scenes/{roadside,overhead,parking_lot,city_street,vehicle_rear}.blend` (re-run when a template changes)
  2. `python render_pipeline/run_batch.py --only 1-20` → per image: open base .blend, apply weather (clear/rain/snow/dusk/night), swap sign artwork, place 50 mm camera, checks, render → `render_pipeline/out/<n>.png`, `out/timings.json`, `out/contact_sheet.png`
- Per-image plan (base scene, weather, artwork + sizes, extras): `render_pipeline/test_plan.json`
- Skipped, need a decision: #11 (generic prohibition disc: no Ontario sign exists), #15 (municipal no-idling sign: no official artwork)
- Wc-5 (#120) still on hold pending the MTO handbook check.
