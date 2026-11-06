"""Re-download the third-party render assets and verify their checksums.

The assets themselves are not in git (see .gitignore). This script rebuilds
tools/question_images/assets/ from the sources pinned in assets.lock.json.

  # 1. Poly Haven HDRIs + textures (CC0), checked against SHA-256 in the lock
  python tools/question_images/fetch_assets.py

  # 2. Sketchfab models (CC BY 4.0) -> assets/*.blend. Needs a free Sketchfab
  #    API token (https://sketchfab.com/settings/password) and Blender:
  set SKETCHFAB_API_TOKEN=...
  blender -b --factory-startup -P tools/question_images/fetch_assets.py -- --models

  --update-lock   record the SHA-256 of what was downloaded (use only after
                  checking the new files by eye; a mismatch otherwise fails)
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
LOCK = os.path.join(HERE, "assets.lock.json")
UA = {"User-Agent": "G1QuestionImages/1.0 (asset fetch)"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get(url, headers=None, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e:  # network hiccups, 429s
            if k == tries - 1:
                raise
            print("  retry", url, e)
            time.sleep(5 * (k + 1))


def fetch(url, dest, want, update, headers=None):
    """Download url to dest unless a verified copy is there. Returns sha256."""
    if os.path.exists(dest) and want and sha256(dest) == want:
        return want
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    data = get(url, headers)
    tmp = dest + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    got = sha256(tmp)
    if want and got != want and not update:
        os.remove(tmp)
        raise SystemExit(f"CHECKSUM MISMATCH {dest}\n  want {want}\n  got  {got}")
    os.replace(tmp, dest)
    return got


def polyhaven(lock, update):
    for entry in lock["polyhaven"]:
        aid, res = entry["id"], entry["res"]
        files = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
        for item in entry["files"]:
            if item["kind"] == "hdri":
                url = files["hdri"][res]["hdr"]["url"]
            else:
                fmts = files[item["map"]][res]
                url = fmts["jpg" if "jpg" in fmts else "png"]["url"]
            dest = os.path.join(ASSETS, "polyhaven", item["path"])
            item["sha256"] = fetch(url, dest, item.get("sha256"), update)
            print("ok", item["path"])


def sketchfab_models(lock, update):
    import bpy  # only under Blender
    token = os.environ.get("SKETCHFAB_API_TOKEN")
    if not token:
        raise SystemExit("set SKETCHFAB_API_TOKEN (free account token) to download the CC BY models")
    import zipfile
    for m in lock["sketchfab"]:
        info = json.loads(get(f"https://api.sketchfab.com/v3/models/{m['uid']}/download",
                              {"Authorization": f"Token {token}"}))
        zpath = os.path.join(ASSETS, "sketchfab", m["name"] + ".zip")
        m["sha256"] = fetch(info["gltf"]["url"], zpath, m.get("sha256"), update)
        out = os.path.join(ASSETS, "sketchfab", m["name"])
        with zipfile.ZipFile(zpath) as z:
            z.extractall(out)
        build_blend(bpy, m, os.path.join(out, "scene.gltf"))


def build_blend(bpy, m, gltf):
    """glTF -> assets/<name>.blend, normalised the way the scenes expect:
    largest dimension = size_m, origin at ground level (trunk base for trees),
    front toward +Y (yaw_deg turns it), all images packed."""
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=gltf)
    objs = list(bpy.context.scene.objects)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in objs if o.type == "MESH" for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    s = m["size_m"] / max(hi - lo)
    if m.get("pivot") == "trunk":
        low = sorted(pts, key=lambda p: p.z)[:max(50, len(pts) // 50)]
        c = sum(low, Vector()) / len(low)
    else:
        c = (lo + hi) / 2
    root = bpy.data.objects.new(m["name"] + "_root", None)
    bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
            o.location -= Vector((c.x, c.y, lo.z))
    root.scale = (s, s, s)
    root.rotation_euler[2] = __import__("math").radians(m.get("yaw_deg", 0))
    coll = bpy.data.collections.new(root.name)
    for o in [root] + objs:
        coll.objects.link(o)
    for img in bpy.data.images:
        if img.source == "FILE" and not img.packed_file:
            img.pack()
    out = os.path.join(ASSETS, m["name"] + ".blend")
    bpy.data.libraries.write(out, {coll}, fake_user=True, compress=True)
    print("built", out)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    update = "--update-lock" in argv
    with open(LOCK, encoding="utf-8") as f:
        lock = json.load(f)
    before = json.dumps(lock, sort_keys=True)
    if "--models" in argv:
        sketchfab_models(lock, update)
    else:
        polyhaven(lock, update)
    # entries without a checksum are pinned on first download (trust on first use);
    # existing checksums only change with --update-lock (a mismatch exits above)
    if json.dumps(lock, sort_keys=True) != before:
        print("lock updated:", LOCK)
        with open(LOCK, "w", encoding="utf-8") as f:
            json.dump(lock, f, indent=1)
            f.write("\n")


main()
