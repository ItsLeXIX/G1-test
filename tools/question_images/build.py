"""Build and render one question image in Blender (headless).

  blender -b --factory-startup -P build.py -- --image 10
  blender -b --factory-startup -P build.py -- --image 10 --quality final --install
  blender -b --factory-startup -P build.py -- --spec '{"template": "roadside", "sign": [["Ra-002.png", 0.75]]}'

--quality  preview (960x400, laptop-safe) | draft | final (2400x1000)
--install  write 1x/2x/3x PNGs into the app's imageset (final only)
--save-blend  also save the .blend next to the preview, for tweaking by hand
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from g1scenes import templates  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
IMAGESETS = os.path.join(REPO, "G1 test", "Assets.xcassets", "QuestionsImages")
SCALES = {"1x": 800, "2x": 1600, "3x": 2400}   # widths; heights keep 2.4:1


def load_spec(args):
    if args.spec:
        return json.loads(args.spec)
    with open(os.path.join(HERE, "manifest.json")) as f:
        manifest = json.load(f)
    spec = manifest["images"][str(args.image)]
    if not spec.get("sign") and spec["template"] not in ("intersection_aerial", "hand_signal"):
        raise SystemExit(f"image {args.image}: sign artwork not assigned yet in manifest.json")
    return spec


def install(name, rendered_path):
    """Replace the imageset's PNGs with fresh 1x/2x/3x files."""
    folder = os.path.join(IMAGESETS, f"{name}.imageset")
    if not os.path.isdir(folder):
        raise SystemExit(f"no imageset {folder}")
    for f in os.listdir(folder):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            os.remove(os.path.join(folder, f))
    images = []
    for scale, width in SCALES.items():
        fname = f"{name}.png" if scale == "1x" else f"{name}@{scale}.png"
        img = bpy.data.images.load(rendered_path)
        if img.size[0] != width:
            img.scale(width, round(width / 2.4))
        img.filepath_raw = os.path.join(folder, fname)
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        images.append({"filename": fname, "idiom": "universal", "scale": scale})
    with open(os.path.join(folder, "Contents.json"), "w") as f:
        json.dump({"images": images, "info": {"author": "xcode", "version": 1}}, f, indent=2)
    print("installed", folder)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--spec")
    ap.add_argument("--quality", default="preview", choices=["preview", "draft", "final"])
    ap.add_argument("--out")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--save-blend", action="store_true")
    ap.add_argument("--no-render", action="store_true", help="build the scene only (cheap check)")
    args = ap.parse_args(argv)
    spec = load_spec(args)
    tpl = templates.get(spec["template"])
    tpl.build(spec, args.quality)

    out = args.out or os.path.join(HERE, "previews", f"{args.image or 'spec'}_{args.quality}.png")
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(out)[0] + ".blend")
    if args.no_render:
        print("built", spec["template"], "objects:", len(bpy.data.objects))
        return
    sc = bpy.context.scene
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)
    if args.install:
        if args.quality != "final":
            raise SystemExit("--install needs --quality final")
        install(args.image, out)


main()
