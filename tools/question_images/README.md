# Question image renderer

Builds the picture for every sign question in `G1 test/questions.json` as a
Blender scene, renders it, and installs it into the app's imageset.

Everything is procedural (no texture downloads), so a preview renders in
about 10 s using about 1.5 GB of RAM. Final renders are meant for a
stronger PC.

## Layout

| Path | What it is |
|---|---|
| `build.py` | Entry point: builds one image's scene and renders it |
| `manifest.json` | One entry per image (asset name → template + settings + sign artwork) |
| `g1scenes/templates/` | The 11 scene types (see below) |
| `g1scenes/roads.py` | Road cross-sections along a path: curves, hills, gravel, side roads, rail |
| `g1scenes/props.py` | Trees, houses, buildings, cars, farm wagon, driver's arm, signals, bridge, rock cut… |
| `g1scenes/signs.py` | Sign panels from official artwork + posts, overhead mounts, decals |
| `g1scenes/env.py` | Sky/sun, weather presets, camera framing, render settings |
| `signs/` | Official sign artwork as PNG (rasterised from the Commons OTM SVGs) |
| `assets/` | Optional real models that replace the procedural stand-ins (see below) |
| `previews/` | Render output (git-ignored) |

## Scene templates

| Template | Used for |
|---|---|
| `roadside` | Sign on a post beside a road: `suburban`, `rural` or `construction`, with features (curves, hills, gravel ahead, side road, signals, rail, bridge, overpass, rock cut, median island, lane drop, crosswalk, cones) |
| `overhead` | Sign hung over the lanes: city mast arm or highway truss; optional two-way left-turn lane markings |
| `city_street` | Downtown street with buildings: one-way, bike lane, parking, pedestrian crossover, school |
| `parking_lot` | Lot in front of a plaza; optional accessible stalls |
| `highway` | 400-series freeway, sign on the shoulder |
| `guide_sign` | Large green guide/distance sign on a provincial highway |
| `vehicle_rear` | Following a vehicle: farm wagon with SMV emblem, or a car at a stop sign or one-way street |
| `hand_signal` | Driver's arm out of the window: `left`, `right`, `stop` |
| `railway_crossing` | Level crossing with crossbuck, flashing lights and tracks |
| `intersection_aerial` | High view of a 4-way intersection with path arrows (question 161) |
| `marking_aerial` | High view of a pavement marking (sharrow) |

Weather for any template: `"weather": "clear" | "overcast" | "rain" | "snow" | "night"`.

## Running

Blender 5.2 must be installed. On Windows use `blender.exe`.

```sh
cd tools/question_images

# quick preview of one image (960x400)
blender -b --factory-startup -P build.py -- --image 10

# try any scene without touching the manifest
blender -b --factory-startup -P build.py -- --spec '{"template":"roadside","setting":"rural","weather":"snow","sign":[["Ra-002.png",0.75]]}'

# final 2400x1000 render, installed into "G1 test/Assets.xcassets/QuestionsImages/10.imageset"
blender -b --factory-startup -P build.py -- --image 10 --quality final --install
```

`--install` replaces the imageset's PNGs with `N.png` (800×333),
`N@2x.png` (1600×667) and `N@3x.png` (2400×1000) and rewrites
`Contents.json`. The asset name doesn't change, so `questions.json` needs no edits.

Add `--save-blend` to keep the `.blend` file for hand-tweaking in the Blender UI.
Add `--no-render` to check that a scene builds without rendering anything.

Render one image per Blender process (as above), so memory is released between images.

## Sign artwork

`manifest.json` → `"sign": [["file.png", width_m], …]`, listed top to bottom
(main sign first, then tabs). Each file must be the official Ontario sign
artwork from the Wikimedia Commons `CA-ON road sign …` set (Ontario Traffic
Manual numbering), rasterised at least 1600 px tall, e.g.:

```sh
rsvg-convert -h 1600 -a "CA-ON road sign Ra-002.svg" -o signs/Ra-002.png
```

The artwork goes onto the panel unchanged. Use the real-world size from the
OTM for `width_m`, e.g. 0.75 for a yield sign, or 0.6/0.75 for most
regulatory and warning signs.

Images whose `sign` is still `null` won't build from the manifest until
their artwork is assigned. The `need` field says which sign to source.

## Better models on the PC (optional)

Put glTF or `.blend` files in `assets/` and they are used automatically instead of the
procedural stand-ins:

| File | Replaces |
|---|---|
| `assets/car_sedan.glb`, `assets/car_suv.glb` | generic cars (no logos) |
| `assets/farm_wagon.glb` | hay wagon in the SMV scene |

Models must be unbranded (no logos or badges), scaled in metres, with the
front facing +Y and the origin at ground level.
